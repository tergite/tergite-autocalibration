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
from numpy.linalg import inv
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix

from tergite_autocalibration.config.settings import REDIS_CONNECTION
from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.tools.mss.convert import structured_redis_storage


class OptimalROAmplitudeQubitAnalysis(BaseQubitAnalysis):

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}

    def analyse_qubit(self):
        self.amplitude_coord = self._get_coord("amplitudes")
        self.state_coord = self._get_coord("state")
        self.loop_coord = self._get_coord("loops")

        breakpoint()
        self.S21 = self.S21.stack(shots=[self.loop_coord, self.state_coord])
        self.qubit_states = self.S21[self.state_coord].values
        self.amplitudes = self.S21.coords[self.amplitude_coord]
        self.fit_results = {}

    def _get_coord(self, keyword):
        """Helper method to get coordinate matching the keyword."""
        for coord in self.dataset.coords:
            if keyword in str(coord):
                return coord
        raise ValueError(f"Coordinate for {keyword} not found in dataset")

    def IQ(self, index: int):
        """Extracts I/Q components from the dataset at a given index."""
        IQ_complex = self.S21[self.data_var].isel(
            {self.amplitude_coord: [index]}
        )  # Use `.isel()` to index correctly
        I = IQ_complex.real.values.flatten()
        Q = IQ_complex.imag.values.flatten()
        return np.array([I, Q]).T

    def run_initial_fitting(self):
        self.fidelities = []
        self.cms = []

        y = self.qubit_states
        n_states = len(y)

        self.lda = LinearDiscriminantAnalysis(solver="svd", store_covariance=True)

        for index, ro_amplitude in enumerate(self.amplitudes):
            iq = self.IQ(index)
            breakpoint()
            y_pred = self.lda.fit(iq, y).predict(iq)

            cm_norm = confusion_matrix(y, y_pred, normalize="true")
            assignment = np.trace(cm_norm) / n_states
            self.fidelities.append(assignment)
            self.cms.append(cm_norm)

        self.optimal_index = np.argmax(self.fidelities)
        self.optimal_amplitude = self.amplitudes.values[self.optimal_index]
        self.optimal_inv_cm = inv(self.cms[self.optimal_index])

        return

    def primary_plotter(self, ax):
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


class Three_Class_Boundary:
    def __init__(self, lda: LinearDiscriminantAnalysis):
        if len(lda.classes_) != 3:
            raise ValueError("The Classifcation classes are not 3.")
        A0 = lda.coef_[0][0]
        B0 = lda.coef_[0][1]
        A1 = lda.coef_[1][0]
        B1 = lda.coef_[1][1]
        A2 = lda.coef_[2][0]
        B2 = lda.coef_[2][1]
        slope0 = -A0 / B0
        slope1 = -A1 / B1
        slope2 = -A2 / B2
        intercept0 = lda.intercept_[0]
        intercept1 = lda.intercept_[1]
        intercept2 = lda.intercept_[2]
        y_intercept0 = intercept0 / B0
        y_intercept1 = intercept1 / B1
        y_intercept2 = intercept2 / B2
        self.slopes = (slope0, slope1, slope2)
        self.y_intercepts = (y_intercept0, y_intercept1, y_intercept2)

    def intersection_I(self, index_a: int, index_b: int):
        numerator = self.y_intercepts[index_a] - self.y_intercepts[index_b]
        denominator = self.slopes[index_a] - self.slopes[index_b]
        return numerator / denominator

    def intersection_Q(self, index_a: int, index_b: int):
        numerator = self.y_intercepts[index_a] - self.y_intercepts[index_b]
        denominator = self.slopes[index_a] - self.slopes[index_b]
        return (
            self.slopes[index_a] * numerator / denominator - self.y_intercepts[index_a]
        )

    def omega(self, index_a: int, index_b: int):
        """
        Be careful: angle defined in the [0,360) range
        """
        i_point = self.intersection_I(index_a, index_b)
        q_point = self.intersection_Q(index_a, index_b)
        omega_in_rad = np.arctan2(
            [q_point - self.centroid[1]], [i_point - self.centroid[0]]
        )
        omega = (np.rad2deg(omega_in_rad) + 360) % 360
        return omega[0]

    @property
    def centroid(self):
        centroid_I = (
            self.intersection_I(0, 1)
            + self.intersection_I(1, 2)
            + self.intersection_I(2, 0)
        )
        centroid_Q = (
            self.intersection_Q(0, 1)
            + self.intersection_Q(1, 2)
            + self.intersection_Q(2, 0)
        )
        return (centroid_I / 3, centroid_Q / 3)

    @property
    def omega_01(self):
        return self.omega(0, 1)

    @property
    def omega_12(self):
        return self.omega(1, 2)

    @property
    def omega_20(self):
        return self.omega(2, 0)

    def boundary_line(self, class_a, class_b) -> tuple[np.ndarray, np.ndarray]:
        i_point = self.intersection_I(class_a, class_b)
        q_point = self.intersection_Q(class_a, class_b)
        i_values = np.linspace(self.centroid[0], i_point, 100)
        boundary_slope = (q_point - self.centroid[1]) / (i_point - self.centroid[0])
        return (
            i_values,
            boundary_slope * (i_values - self.centroid[0]) + self.centroid[1],
        )


class OptimalROTwoStateAmplitudeQubitAnalysis(OptimalROAmplitudeQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        super().analyse_qubit()
        self.run_initial_fitting()
        inv_cm_str = ",".join(
            str(element) for element in list(self.optimal_inv_cm.flatten())
        )

        y = self.qubit_states

        optimal_IQ = self.IQ(self.optimal_index)
        optimal_y = self.lda.fit(optimal_IQ, y).predict(optimal_IQ)

        # determining the discriminant line from the canonical form Ax + By + intercept = 0
        A = self.lda.coef_[0][0]
        B = self.lda.coef_[0][1]
        intercept = self.lda.intercept_
        self.lamda = -A / B
        theta = np.rad2deg(np.arctan(self.lamda))
        threshold = np.abs(intercept) / np.sqrt(A**2 + B**2)
        threshold = threshold[0]

        self.y_intecept = +intercept / B

        self.x_space = np.linspace(optimal_IQ[:, 0].min(), optimal_IQ[:, 0].max(), 100)
        self.y_limits = (optimal_IQ[:, 1].min(), optimal_IQ[:, 1].max())

        true_positives = y == optimal_y
        tp0 = true_positives[y == 0]
        tp1 = true_positives[y == 1]
        IQ0 = optimal_IQ[y == 0]  # IQ when sending 0
        IQ1 = optimal_IQ[y == 1]  # IQ when sending 1

        rotation_angle = np.pi / 2 - theta_rad
        rotation_matrix = np.array(
            [
                [np.cos(rotation_angle), -np.sin(rotation_angle)],
                [np.sin(rotation_angle), np.cos(rotation_angle)],
            ]
        )
        mirror_rotation = np.array(
            [
                [np.cos(np.pi), -np.sin(np.pi)],
                [np.sin(np.pi), np.cos(np.pi)],
            ]
        )

        translated_IQ = optimal_IQ - np.array([0, self.y_intecept[0]])
        rotated_IQ = translated_IQ @ rotation_matrix.T
        # self.y_limits = (optimal_IQ[:, 1].min(), optimal_IQ[:, 1].max())

        # translate point so the y_intecept becomes the origin
        translated_IQ0 = translated_IQ[y == 0]
        translated_IQ1 = translated_IQ[y == 1]
        # @ is the matrix multiplication operator
        rotated_IQ0 = translated_IQ0 @ rotation_matrix.T
        rotated_IQ1 = translated_IQ1 @ rotation_matrix.T

        threshold_direction = theta_rad - np.pi / 2
        center_rotated_I_0 = np.mean(rotated_IQ0[:, 0])

        # probably there is a more elegant solution
        if center_rotated_I_0 > 0:
            rotation_angle = rotation_angle + np.pi
            threshold_direction = threshold_direction + np.pi
            rotated_IQ0 = rotated_IQ0 @ mirror_rotation.T
            rotated_IQ1 = rotated_IQ1 @ mirror_rotation.T
            rotated_IQ = rotated_IQ @ mirror_rotation.T

        self.threshold_point = self.threshold * np.array(
            [np.cos(threshold_direction), np.sin(threshold_direction)]
        )
        self.rotated_IQ0_tp = rotated_IQ0[tp0]  # True Positive when sending 0
        self.rotated_IQ0_fp = rotated_IQ0[~tp0]
        self.rotated_IQ1_tp = rotated_IQ1[tp1]  # True Positive when sending 1
        self.rotated_IQ1_fp = rotated_IQ1[~tp1]
        self.IQ0_tp = IQ0[tp0]  # True Positive when sending 0
        self.IQ0_fp = IQ0[~tp0]
        self.IQ1_tp = IQ1[tp1]  # True Positive when sending 1
        self.IQ1_fp = IQ1[~tp1]

        self.rotated_y_limits = (rotated_IQ[:, 1].min(), rotated_IQ[:, 1].max())
        self.y_limits = (optimal_IQ[:, 1].min(), optimal_IQ[:, 1].max())

        self.rotation_angle = rotation_angle
        self.rotation_angle_degrees = np.rad2deg(rotation_angle)
        print(f"{self.qubit}.measure.acq_rotation = {self.rotation_angle_degrees}")
        print(f"{self.qubit}.measure.acq_threshold = {self.threshold}")

        return [self.optimal_amplitude, self.rotation_angle_degrees, self.threshold]

    def plotter(self, ax, secondary_axes):
        self.primary_plotter(ax)

        iq_axis = secondary_axes[0]
        mark_size = 40
        iq_axis.plot(self.x_space, self.lamda * self.x_space - self.y_intecept, lw=2)
        iq_axis.scatter(
            self.IQ0_tp[:, 0],
            self.IQ0_tp[:, 1],
            marker=".",
            s=mark_size,
            color="red",
            label="send 0 and read 0",
        )
        iq_axis.scatter(
            self.IQ0_fp[:, 0],
            self.IQ0_fp[:, 1],
            marker="x",
            s=mark_size,
            color="orange",
        )
        iq_axis.scatter(
            self.IQ1_tp[:, 0],
            self.IQ1_tp[:, 1],
            marker=".",
            s=mark_size,
            color="blue",
            label="send 1 and read 1",
        )
        iq_axis.scatter(
            self.IQ1_fp[:, 0],
            self.IQ1_fp[:, 1],
            marker="x",
            s=mark_size,
            color="dodgerblue",
        )
        iq_axis.set_ylim(*self.y_limits)

        cm_axis = secondary_axes[1]
        optimal_confusion_matrix = self.cms[self.optimal_index]
        disp = ConfusionMatrixDisplay(confusion_matrix=optimal_confusion_matrix)
        disp.plot(ax=cm_axis)

    def update_redis_trusted_values(self, node: str, this_element: str):
        """
        TODO: This method is a temporary solution to store the discriminator until we switch to ThresholdedAcquisition
        Args:
            node: The parent node
            this_element: Name of the qubit e.g. 'q12'

        Returns:

        """
        super().update_redis_trusted_values(node, this_element)

        # We read coefficients and intercept from the lda model
        coef_0_ = str(float(self.lda.coef_[0][0]))
        coef_1_ = str(float(self.lda.coef_[0][1]))
        intercept_ = str(float(self.lda.intercept_[0]))

        # We update the values in redis
        REDIS_CONNECTION.hset(f"transmons:{this_element}", "lda_coef_0", coef_0_)
        REDIS_CONNECTION.hset(f"transmons:{this_element}", "lda_coef_1", coef_1_)
        REDIS_CONNECTION.hset(f"transmons:{this_element}", "lda_intercept", intercept_)

        # We also update the values in the redis standard storage
        structured_redis_storage("lda_coef_0", this_element.strip("q"), coef_0_)
        structured_redis_storage("lda_coef_1", this_element.strip("q"), coef_1_)
        structured_redis_storage("lda_intercept", this_element.strip("q"), intercept_)


class OptimalROThreeStateAmplitudeQubitAnalysis(OptimalROAmplitudeQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        super().analyse_qubit()
        self.run_initial_fitting()
        inv_cm_str = ",".join(
            str(element) for element in list(self.optimal_inv_cm.flatten())
        )

        y = self.qubit_states

        optimal_IQ = self.IQ(self.optimal_index)
        optimal_y = self.lda.fit(optimal_IQ, y).predict(optimal_IQ)

        self.boundary = Three_Class_Boundary(self.lda)
        self.centroid_I = self.boundary.centroid[0]
        self.centroid_Q = self.boundary.centroid[1]
        self.omega_01 = self.boundary.omega_01
        self.omega_12 = self.boundary.omega_12
        self.omega_20 = self.boundary.omega_20

        true_positives = y == optimal_y
        tp0 = true_positives[y == 0]
        tp1 = true_positives[y == 1]
        tp2 = true_positives[y == 1]
        IQ0 = optimal_IQ[y == 0]  # IQ when sending 0
        IQ1 = optimal_IQ[y == 1]  # IQ when sending 1
        IQ2 = optimal_IQ[y == 2]  # IQ when sending 2

        self.IQ0_tp = IQ0[tp0]  # True Positive when sending 0
        self.IQ0_fp = IQ0[~tp0]
        self.IQ1_tp = IQ1[tp1]  # True Positive when sending 1
        self.IQ1_fp = IQ1[~tp1]
        self.IQ2_tp = IQ2[tp2]  # True Positive when sending 2
        self.IQ2_fp = IQ2[~tp2]
        return [
            self.optimal_amplitude,
            self.centroid_I,
            self.centroid_Q,
            self.omega_01,
            self.omega_12,
            self.omega_20,
            inv_cm_str,
        ]

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
