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

"""
Module containing a class that fits data from a resonator spectroscopy experiment.
"""
import numpy as np
import matplotlib.patches as mpatches
from numpy.linalg import inv
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

from tergite_autocalibration.config.settings import REDIS_CONNECTION
from tergite_autocalibration.lib.base.analysis import BaseQubitAnalysis, BaseAllQubitsAnalysis
from tergite_autocalibration.tools.mss.convert import structured_redis_storage


class OptimalROAmplitudeQubitAnalysis(BaseQubitAnalysis):
    """
    Analysis that  extracts the optimal RO amplitude.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}


    def analyse_qubit(self):
        self.amplitude_coord = self._get_coord("amplitudes")
        self.state_coord = self._get_coord("state")

        self.qubit_states = self.dataset[self.state_coord].values
        self.amplitudes = self.dataset.coords[self.amplitude_coord]
        self.fit_results = {}

    def _get_coord(self, keyword):
        """Helper method to get coordinate matching the keyword."""
        for coord in self.dataset.coords:
            if keyword in str(coord):
                return coord
        raise ValueError(f"Coordinate for {keyword} not found in dataset")

    def IQ(self, index: int):
        """Extracts I/Q components from the dataset at a given index."""
        IQ_complex = self.S21[self.data_var].isel({self.amplitude_coord: index}) # Use `.isel()` to index correctly
        I = IQ_complex.real.values.flatten()
        Q = IQ_complex.imag.values.flatten()
        return np.array([I, Q]).T

    def run_initial_fitting(self):
        self.fidelities = []
        self.cms = []

        y = self.qubit_states
        n_states = len(np.unique(y))

        self.lda = LinearDiscriminantAnalysis(solver="svd", store_covariance=True)

        for index, ro_amplitude in enumerate(self.amplitudes):
            iq = self.IQ(index)
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
        self.plotter(primary_axis, secondary_axes)  # Assuming node_analysis object is available

        # Customize plot as needed
        handles, labels = primary_axis.get_legend_handles_labels()
        patch = mpatches.Patch(color="red", label=f"{self.qubit}")
        handles.append(patch)
        primary_axis.legend(handles=handles, fontsize="small")

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

        self.IQ0_tp = IQ0[tp0]  # True Positive when sending 0
        self.IQ0_fp = IQ0[~tp0]
        self.IQ1_tp = IQ1[tp1]  # True Positive when sending 1
        self.IQ1_fp = IQ1[~tp1]

        return [self.optimal_amplitude, theta, threshold]

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

    def update_redis_trusted_values(
        self, node: str, this_element: str, transmon_parameters: list
    ):
        """
        TODO: This method is a temporary solution to store the discriminator until we switch to ThresholdedAcquisition
        Args:
            node: The parent node
            this_element: Name of the qubit e.g. 'q12'
            transmon_parameters: list of qois

        Returns:

        """
        super().update_redis_trusted_values(node, this_element, transmon_parameters)

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
        return [self.optimal_amplitude, inv_cm_str]

    def plotter(self, ax, secondary_axes):
        self.primary_plotter(ax)

        iq_axis = secondary_axes[0]
        mark_size = 40
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
        iq_axis.scatter(
            self.IQ2_tp[:, 0], self.IQ2_tp[:, 1], marker=".", s=mark_size, color="green"
        )
        iq_axis.scatter(
            self.IQ2_fp[:, 0],
            self.IQ2_fp[:, 1],
            marker="x",
            s=mark_size,
            color="lime",
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

