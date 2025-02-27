# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import matplotlib.patches as mpatches
import numpy as np
import xarray as xr
from numpy.linalg import inv
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.lib.utils.analysis_models import (
    ThreeClassBoundary,
    TwoClassBoundary,
)
from tergite_autocalibration.utils.dto.qoi import QOI


class OptimalROAmplitudeQubitAnalysis(BaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}

    def analyse_qubit(self):
        for coord in self.S21[self.data_var].coords:
            if "amplitudes" in coord:
                self.amplitude_coord = coord
                self.amplitudes = self.S21.coords[coord]
                self.number_of_amplitudes = self.amplitudes.size
            elif "state" in coord:
                self.state_coord = coord
                self.unique_qubit_states = self.S21[coord].values
            elif "loops" in coord:
                self.loop_coord = coord
            else:
                raise ValueError("Coordinate not found in dataset")

        self.S21_stacked = self.S21.stack(shots=[self.loop_coord, self.state_coord])
        self.qubit_states = self.S21_stacked[self.state_coord].values
        self.fit_results = {}

    def IQ(self, index: int) -> np.ndarray:
        """Extracts I/Q components from the dataset at a given index."""

        IQ_complex = self.S21_stacked[self.data_var].isel(
            {self.amplitude_coord: index}
        )  # Use `.isel()` to index correctly
        I = IQ_complex.real.values
        Q = IQ_complex.imag.values
        return np.array([I, Q]).T

    def run_initial_fitting(self):
        """
        Classify all iq points for all amplitudes and store them in
        corresponding dataArrays.
        """
        # TODO: replace the amplitude for loop with a dataset mask
        self.fidelities = []
        self.cms = []

        states_sent = self.qubit_states

        self.lda = LinearDiscriminantAnalysis(solver="svd", store_covariance=True)

        array_iq0_tp = xr.DataArray().expand_dims({self.amplitude_coord: []})
        array_iq0_fp = xr.DataArray().expand_dims({self.amplitude_coord: []})
        array_iq1_tp = xr.DataArray().expand_dims({self.amplitude_coord: []})
        array_iq1_fp = xr.DataArray().expand_dims({self.amplitude_coord: []})
        for index, ro_amplitude in enumerate(self.amplitudes):
            iq = self.IQ(index)
            classified_states = self.lda.fit(iq, states_sent).predict(iq)

            true_positives = states_sent == classified_states
            tp0 = true_positives[states_sent == 0]
            tp1 = true_positives[states_sent == 1]
            IQ0 = iq[states_sent == 0]  # IQ when sending 0
            IQ1 = iq[states_sent == 1]  # IQ when sending 1

            IQ0_tp = xr.DataArray(
                IQ0[tp0],
                name="IQ0_tp",
                coords={"shots": np.arange(len(IQ0[tp0])), "re_im": ["re", "im"]},
            ).expand_dims(
                {self.amplitude_coord: [ro_amplitude]}
            )  # True Positive when sending 0

            IQ0_fp = xr.DataArray(
                IQ0[~tp0],
                name="IQ0_fp",
                coords={"shots": np.arange(len(IQ0[~tp0])), "re_im": ["re", "im"]},
            ).expand_dims({self.amplitude_coord: [ro_amplitude]})

            IQ1_tp = xr.DataArray(
                IQ1[tp1],
                name="IQ1_tp",
                coords={"shots": np.arange(len(IQ1[tp1])), "re_im": ["re", "im"]},
            ).expand_dims(
                {self.amplitude_coord: [ro_amplitude]}
            )  # True Positive when sending 1

            IQ1_fp = xr.DataArray(
                IQ1[~tp1],
                name="IQ1_fp",
                coords={"shots": np.arange(len(IQ1[~tp1])), "re_im": ["re", "im"]},
            ).expand_dims({self.amplitude_coord: [ro_amplitude]})
            array_iq0_tp = xr.concat([IQ0_tp, array_iq0_tp], dim=self.amplitude_coord)
            array_iq0_fp = xr.concat([IQ0_fp, array_iq0_fp], dim=self.amplitude_coord)
            array_iq1_tp = xr.concat([IQ1_tp, array_iq1_tp], dim=self.amplitude_coord)
            array_iq1_fp = xr.concat([IQ1_fp, array_iq1_fp], dim=self.amplitude_coord)

            cm_norm = confusion_matrix(states_sent, classified_states, normalize="true")
            assignment = np.trace(cm_norm) / len(self.unique_qubit_states)
            self.fidelities.append(assignment)
            self.cms.append(cm_norm)

        self.iq0_tp = array_iq0_tp
        self.iq0_fp = array_iq0_fp
        self.iq1_tp = array_iq1_tp
        self.iq1_fp = array_iq1_fp
        self.optimal_index = np.argmax(self.fidelities)
        self.optimal_amplitude = self.amplitudes.values[self.optimal_index]
        self.optimal_inv_cm = inv(self.cms[self.optimal_index])

        return

    def primary_plotter(self, ax):
        punchout_amplitude = float(
            REDIS_CONNECTION.hget(f"transmons:{self.qubit}", "measure:pulse_amp")
        )
        ax.axvline(punchout_amplitude, color="black", label="punchout value")
        ax.set_xlabel("RO amplitude")
        ax.set_ylabel("assignment fidelity")
        ax.plot(self.amplitudes, self.fidelities)
        ax.plot(self.optimal_amplitude, self.fidelities[self.optimal_index], "*", ms=14)
        ax.grid()

    def _plot(self, primary_axis, secondary_axes):
        self.plotter(
            primary_axis, secondary_axes
        )  # Assuming node_analysis object is available

        # Customize plot as needed
        handles, labels = primary_axis.get_legend_handles_labels()
        patch = mpatches.Patch(color="red", label=f"{self.qubit}")
        handles.append(patch)
        primary_axis.legend(handles=handles, fontsize="small")


class OptimalROTwoStateAmplitudeQubitAnalysis(OptimalROAmplitudeQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def align_on_y_axis(
        self,
        iq_points: np.ndarray,
        classified_states: np.ndarray,
        boundary_angle_rad: float,
        absolute_threshold: float,
    ) -> tuple[np.ndarray, float, float]:
        """
        Translate and rotate the IQ samples so that all the |0> are on the I<0 semi-plane
        and all the |1> states are on the I>0 semi plane in accordance to Quantify Scheduler
        convention for Thresholded Acquisitions
        """
        rotation_angle_rad = np.pi / 2 - boundary_angle_rad
        rotation_matrix = np.array(
            [
                [np.cos(rotation_angle_rad), -np.sin(rotation_angle_rad)],
                [np.sin(rotation_angle_rad), np.cos(rotation_angle_rad)],
            ]
        )
        mirror_rotation = np.array(
            [
                [np.cos(np.pi), -np.sin(np.pi)],
                [np.sin(np.pi), np.cos(np.pi)],
            ]
        )
        # translated_IQ = iq_points - np.array([0, y_intercept])
        translated_IQ = iq_points
        rotated_IQ = translated_IQ @ rotation_matrix.T

        rotated_IQ0 = rotated_IQ[classified_states == 0]
        rotated_IQ1 = rotated_IQ[classified_states == 1]
        center_of_rotated_I_0 = np.mean(rotated_IQ0[:, 0])
        center_of_rotated_I_1 = np.mean(rotated_IQ1[:, 0])
        if center_of_rotated_I_0 > center_of_rotated_I_1:
            rotation_angle_rad = rotation_angle_rad + np.pi
            rotated_IQ = rotated_IQ @ mirror_rotation.T

        rotated_IQ0 = rotated_IQ[classified_states == 0]
        rotated_IQ1 = rotated_IQ[classified_states == 1]
        center_of_rotated_I_0 = np.mean(rotated_IQ0[:, 0])
        center_of_rotated_I_1 = np.mean(rotated_IQ1[:, 0])
        if center_of_rotated_I_0 < absolute_threshold < center_of_rotated_I_1:
            threshold = absolute_threshold
        else:
            threshold = -absolute_threshold

        if not center_of_rotated_I_0 < threshold < center_of_rotated_I_1:
            raise ValueError("threshold is at an imporoper value")

        return rotated_IQ, rotation_angle_rad, threshold

    def analyse_qubit(self):
        super().analyse_qubit()
        self.run_initial_fitting()
        inv_cm_str = ",".join(
            str(element) for element in list(self.optimal_inv_cm.flatten())
        )

        states = self.qubit_states

        optimal_IQ = self.IQ(self.optimal_index)
        classified_states = self.lda.fit(optimal_IQ, states).predict(optimal_IQ)

        true_positives = states == classified_states
        tp0 = true_positives[states == 0]
        tp1 = true_positives[states == 1]
        IQ0 = optimal_IQ[states == 0]  # IQ when sending 0
        IQ1 = optimal_IQ[states == 1]  # IQ when sending 1

        boundary = TwoClassBoundary(self.lda)
        self.theta_rad = boundary.theta_rad
        self.y_intercept = boundary.y_intercept
        self.absolute_threshold = boundary.threshold
        self.centers = boundary.centers
        self.lamda = boundary.lamda
        boundary_angle_rad = self.theta_rad

        aligned_IQ, rotation_angle_rad, threshold = self.align_on_y_axis(
            optimal_IQ, classified_states, boundary_angle_rad, self.absolute_threshold
        )
        self.threshold = threshold

        aligned_IQ0 = aligned_IQ[states == 0]
        aligned_IQ1 = aligned_IQ[states == 1]
        self.rotated_IQ0_tp = aligned_IQ0[tp0]  # True Positive when sending 0
        self.rotated_IQ0_fp = aligned_IQ0[~tp0]
        self.rotated_IQ1_tp = aligned_IQ1[tp1]  # True Positive when sending 1
        self.rotated_IQ1_fp = aligned_IQ1[~tp1]

        self.IQ0_tp = IQ0[tp0]  # True Positive when sending 0
        self.IQ0_fp = IQ0[~tp0]
        self.IQ1_tp = IQ1[tp1]  # True Positive when sending 1
        self.IQ1_fp = IQ1[~tp1]

        self.rotated_y_limits = (aligned_IQ[:, 1].min(), aligned_IQ[:, 1].max())

        self.x_space = np.linspace(optimal_IQ[:, 0].min(), optimal_IQ[:, 0].max(), 100)
        x_min = min(optimal_IQ[:, 0].min(), 0)
        x_max = max(optimal_IQ[:, 0].max(), 0)
        y_min = min(optimal_IQ[:, 1].min(), 0)
        y_max = max(optimal_IQ[:, 1].max(), 0)
        delta_x = x_max - x_min
        delta_y = y_max - y_min

        delta = max(delta_x, delta_y)
        center_distance = np.linalg.norm(self.centers[0] - self.centers[1])
        self.x_limits = (
            x_min - center_distance / 2,
            x_min + delta + center_distance / 2,
        )
        self.y_limits = (
            y_min - center_distance / 2,
            y_min + delta + center_distance / 2,
        )

        self.rotation_angle = rotation_angle_rad
        self.rotation_angle_degrees = np.rad2deg(rotation_angle_rad)

        analysis_successful = True
        analysis_result = {
            "measure_2state_opt:pulse_amp": {
                "value": self.optimal_amplitude,
                "error": 0
            },
            "measure_2state_opt:acq_rotation": {
                "value": self.rotation_angle_degrees,
                "error": 0
            },
            "measure_2state_opt:acq_threshold": {
                "value": self.threshold,
                "error": 0
            },
            "lda_coef_0": {
                "value": str(float(self.lda.coef_[0][0])),
                "error": 0
            },
            "lda_coef_1": {
                "value": str(float(self.lda.coef_[0][1])),
                "error": 0
            },
            "lda_intercept": {
                "value": str(float(self.lda.intercept_[0])),
                "error": 0
            }
        }
        qoi = QOI(analysis_result, analysis_successful)
        return qoi

    def plotter(self, ax, secondary_axes):
        self.primary_plotter(ax)
        iq_axis = secondary_axes[0]

        mark_size = 40

        optimal_iq_axis = secondary_axes[0]
        optimal_iq_axis.set_xlim(*self.x_limits)
        optimal_iq_axis.set_ylim(*self.y_limits)
        optimal_iq_axis.scatter(
            self.IQ0_tp[:, 0],
            self.IQ0_tp[:, 1],
            marker=".",
            s=mark_size,
            color="blue",
            label="send 0 and read 0",
        )
        iq_axis.scatter(
            self.IQ0_fp[:, 0],
            self.IQ0_fp[:, 1],
            marker="x",
            s=mark_size,
            color="dodgerblue",
        )
        iq_axis.scatter(
            self.IQ1_tp[:, 0],
            self.IQ1_tp[:, 1],
            marker=".",
            s=mark_size,
            color="red",
            label="send 1 and read 1",
        )
        iq_axis.scatter(
            self.IQ1_fp[:, 0],
            self.IQ1_fp[:, 1],
            marker="x",
            s=mark_size,
            color="orange",
        )
        iq_axis.scatter(
            self.centers[:, 0],
            self.centers[:, 1],
            s=2 * mark_size,
            color="brown",
            zorder=10,
        )
        iq_axis.scatter(
            0,
            self.y_intercept,
            s=2 * mark_size,
            marker="P",
            color="black",
            zorder=11,
        )

        iq_axis.plot(
            self.x_space,
            self.lamda * self.x_space + self.y_intercept,
            lw=2,
            label=f"angle: {self.rotation_angle_degrees:0.1f}" r"$\degree$",
        )
        optimal_iq_axis.legend()
        optimal_iq_axis.axhline(0, color="black")
        optimal_iq_axis.axvline(0, color="black")
        rotated_iq_axis = secondary_axes[1]
        rotated_iq_axis.scatter(
            self.rotated_IQ0_tp[:, 0],
            self.rotated_IQ0_tp[:, 1],
            marker=".",
            s=mark_size,
            color="blue",
            label="send 0 and read 0",
        )
        rotated_iq_axis.scatter(
            self.rotated_IQ0_fp[:, 0],
            self.rotated_IQ0_fp[:, 1],
            marker="x",
            s=mark_size,
            color="dodgerblue",
        )
        rotated_iq_axis.scatter(
            self.rotated_IQ1_tp[:, 0],
            self.rotated_IQ1_tp[:, 1],
            marker=".",
            s=mark_size,
            color="red",
            label="send 1 and read 1",
        )
        rotated_iq_axis.scatter(
            self.rotated_IQ1_fp[:, 0],
            self.rotated_IQ1_fp[:, 1],
            marker="x",
            s=mark_size,
            color="orange",
        )
        rotated_iq_axis.axvline(
            self.threshold,
            color="purple",
            lw=3,
            label=f"threshold: {self.threshold:0.4f}",
        )

        rotated_iq_axis.legend()
        rotated_iq_axis.axhline(0, color="black")
        rotated_iq_axis.axvline(0, color="black")


class OptimalROThreeStateAmplitudeQubitAnalysis(OptimalROAmplitudeQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        """
        classify the three states for each RO amplitude
        and return the RO amplitude that gives the maximum three state classification fidelity
        as well as the defining parameters for the optimal three state boundary
        returns
        -------
        optimal_amplitude: float
            amplitude of the RO pulse that gives optimal fidelity
        centroid_I: float
            I coordinate of the centroid defined by the class boundaries
        centroid_Q: float
            Q coordinate of the centroid defined by the class boundaries
        omega_01: float \in [0,360) degrees
            defining angle for the |0> - |1> boundary
        omega_12: float \in [0,360) degrees
            defining angle for the |1> - |2> boundary
        omega_20 \in [0,360) degrees,
            defining angle for the |2> - |0> boundary
        inv_cm_str: str
            string encoding of the confusion matrix
        """
        super().analyse_qubit()
        self.run_initial_fitting()
        inv_cm_str = ",".join(
            str(element) for element in list(self.optimal_inv_cm.flatten())
        )

        y = self.qubit_states

        optimal_IQ = self.IQ(self.optimal_index)
        optimal_y = self.lda.fit(optimal_IQ, y).predict(optimal_IQ)

        self.boundary = ThreeClassBoundary(self.lda)
        self.centroid_I = self.boundary.centroid[0]
        self.centroid_Q = self.boundary.centroid[1]
        self.omega_01 = self.boundary.omega_01
        self.omega_12 = self.boundary.omega_12
        self.omega_20 = self.boundary.omega_20

        true_positives = y == optimal_y
        tp0 = true_positives[y == 0]
        tp1 = true_positives[y == 1]
        tp2 = true_positives[y == 2]
        IQ0 = optimal_IQ[y == 0]  # IQ when sending 0
        IQ1 = optimal_IQ[y == 1]  # IQ when sending 1
        IQ2 = optimal_IQ[y == 2]  # IQ when sending 2

        self.IQ0_tp = IQ0[tp0]  # True Positive when sending 0
        self.IQ0_fp = IQ0[~tp0]
        self.IQ1_tp = IQ1[tp1]  # True Positive when sending 1
        self.IQ1_fp = IQ1[~tp1]
        self.IQ2_tp = IQ2[tp2]  # True Positive when sending 2
        self.IQ2_fp = IQ2[~tp2]

        analysis_successful = True
        analysis_result = {
            "measure_3state_opt:pulse_amp": {
                "value": self.optimal_amplitude,
                "error": 0,
            },
            "centroid_I": {
                "value": self.centroid_I,
                "error": 0,
            },
            "centroid_Q": {
                "value": self.centroid_Q,
                "error": 0,
            },
            "omega_01": {
                "value": self.omega_01,
                "error": 0,
            },
            "omega_12": {
                "value": self.omega_12,
                "error": 0,
            },
            "omega_20": {
                "value": self.omega_20,
                "error": 0,
            },
            "inv_cm_opt": {
                "value": inv_cm_str,
                "error": 0,
            },
        }
        qoi = QOI(analysis_result, analysis_successful)
        return qoi

    def plotter(self, ax, secondary_axes):
        self.primary_plotter(ax)

        iq_axis = secondary_axes[0]
        mark_size = 40
        iq_axis.scatter(
            self.IQ0_tp[:, 0],
            self.IQ0_tp[:, 1],
            marker=".",
            s=mark_size,
            color="blue",
            label="send 0 and read 0",
        )
        iq_axis.scatter(
            self.IQ0_fp[:, 0],
            self.IQ0_fp[:, 1],
            marker="x",
            s=mark_size,
            color="dodgerblue",
        )
        iq_axis.scatter(
            self.IQ1_tp[:, 0],
            self.IQ1_tp[:, 1],
            marker=".",
            s=mark_size,
            color="red",
            label="send 1 and read 1",
        )
        iq_axis.scatter(
            self.IQ1_fp[:, 0],
            self.IQ1_fp[:, 1],
            marker="x",
            s=mark_size,
            color="orange",
        )
        iq_axis.scatter(
            self.IQ2_tp[:, 0],
            self.IQ2_tp[:, 1],
            marker=".",
            s=mark_size,
            color="green",
            label="send 2 and read 2",
        )
        iq_axis.scatter(
            self.IQ2_fp[:, 0],
            self.IQ2_fp[:, 1],
            marker="x",
            s=mark_size,
            color="lime",
        )
        iq_axis.plot(
            self.boundary.boundary_line(0, 1)[0],
            self.boundary.boundary_line(0, 1)[1],
            color="blueviolet",
            lw=4,
        )
        iq_axis.plot(
            self.boundary.boundary_line(1, 2)[0],
            self.boundary.boundary_line(1, 2)[1],
            color="firebrick",
            lw=4,
        )
        iq_axis.plot(
            self.boundary.boundary_line(2, 0)[0],
            self.boundary.boundary_line(2, 0)[1],
            color="cyan",
            lw=4,
        )
        iq_axis.scatter(
            self.centroid_I, self.centroid_Q, marker="*", s=480, color="black", zorder=2
        )

        cm_axis = secondary_axes[1]
        optimal_confusion_matrix = self.cms[self.optimal_index]
        disp = ConfusionMatrixDisplay(confusion_matrix=optimal_confusion_matrix)
        disp.plot(ax=cm_axis)


class OptimalROTwoStateAmplitudeNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = OptimalROTwoStateAmplitudeQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.plots_per_qubit = 3

    def _fill_plots(self):
        for index, analysis in enumerate(self.qubit_analyses):
            primary_plot_row = self.plots_per_qubit * (index // self.column_grid)
            primary_axis = self.axs[primary_plot_row, index % self.column_grid]

            list_of_secondary_axes = []
            for plot_indx in range(1, self.plots_per_qubit):
                secondary_plot_row = primary_plot_row + plot_indx
                list_of_secondary_axes.append(
                    self.axs[secondary_plot_row, index % self.column_grid]
                )

            analysis._plot(primary_axis, list_of_secondary_axes)


class OptimalROThreeStateAmplitudeNodeAnalysis(OptimalROTwoStateAmplitudeNodeAnalysis):
    single_qubit_analysis_obj = OptimalROThreeStateAmplitudeQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
