"""
Module containing a class that fits data from a resonator spectroscopy experiment.
"""
import numpy as np
import redis
import xarray as xr
from numpy.linalg import inv
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

from tergite_calibration.config.settings import REDIS_CONNECTION
from tergite_calibration.lib.analysis_base import BaseAnalysis
from tergite_calibration.utils.convert import structured_redis_storage


class OptimalROAmplitudeAnalysis(BaseAnalysis):
    """
    Analysis that  extracts the optimal RO amplitude.
    """

    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        self.dataset = dataset
        self.qubit = dataset.attrs['qubit']
        self.data_var = list(dataset.data_vars.keys())[0]
        self.S21 = self.dataset[self.data_var]

        for coord in dataset.coords:
            if 'amplitudes' in str(coord):
                self.amplitude_coord = coord
            elif 'state' in str(coord):
                self.state_coord = coord
            elif 'shot' in str(coord):
                self.shot_coord = coord
        self.qubit_states = dataset[self.state_coord].values
        self.amplitudes = dataset.coords[self.amplitude_coord]
        self.fit_results = {}

    def IQ(self, index: int):
        IQ_complex = self.S21.isel({self.amplitude_coord: [index]})
        I = IQ_complex.real.values.flatten()
        Q = IQ_complex.imag.values.flatten()
        IQ_samples = np.array([I, Q]).T
        return IQ_samples

    def run_initial_fitting(self):
        self.fidelities = []
        self.cms = []

        y = self.qubit_states
        n_states = len(np.unique(y))

        self.lda = LinearDiscriminantAnalysis(solver="svd", store_covariance=True)

        for index, ro_amplitude in enumerate(self.amplitudes):
            iq = self.IQ(index)
            y_pred = self.lda.fit(iq, y).predict(iq)

            cm_norm = confusion_matrix(y, y_pred, normalize='true')
            assignment = np.trace(cm_norm) / n_states
            self.fidelities.append(assignment)
            self.cms.append(cm_norm)

        self.optimal_index = np.argmax(self.fidelities)
        self.optimal_amplitude = self.amplitudes.values[self.optimal_index]
        self.optimal_inv_cm = inv(self.cms[self.optimal_index])

        return

    def primary_plotter(self, ax):
        this_qubit = self.dataset.attrs['qubit']
        ax.set_xlabel('RO amplitude')
        ax.set_ylabel('assignment fidelity')
        ax.plot(self.amplitudes, self.fidelities)
        ax.plot(self.optimal_amplitude, self.fidelities[self.optimal_index], '*', ms=14)
        ax.grid()


class OptimalRO_Two_state_AmplitudeAnalysis(OptimalROAmplitudeAnalysis):
    def __init__(self, dataset: xr.Dataset):
        self.dataset = dataset
        super().__init__(self.dataset)

    def run_fitting(self):
        self.run_initial_fitting()
        inv_cm_str = ",".join(str(element) for element in list(self.optimal_inv_cm.flatten()))

        y = self.qubit_states

        optimal_IQ = self.IQ(self.optimal_index)
        optimal_y = self.lda.fit(optimal_IQ, y).predict(optimal_IQ)

        # determining the discriminant line from the canonical form Ax + By + intercept = 0
        A = self.lda.coef_[0][0]
        B = self.lda.coef_[0][1]
        intercept = self.lda.intercept_
        self.lamda = - A / B
        theta = np.rad2deg(np.arctan(self.lamda))
        threshold = np.abs(intercept) / np.sqrt(A ** 2 + B ** 2)
        threshold = threshold[0]

        self.y_intecept = + intercept / B

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
        iq_axis.scatter(self.IQ0_tp[:, 0], self.IQ0_tp[:, 1], marker=".", s=mark_size, color="red",
                        label='send 0 and read 0')
        iq_axis.scatter(self.IQ0_fp[:, 0], self.IQ0_fp[:, 1], marker="x", s=mark_size, color="orange", )
        iq_axis.scatter(self.IQ1_tp[:, 0], self.IQ1_tp[:, 1], marker=".", s=mark_size, color="blue",
                        label='send 1 and read 1')
        iq_axis.scatter(self.IQ1_fp[:, 0], self.IQ1_fp[:, 1], marker="x", s=mark_size, color="dodgerblue", )
        iq_axis.set_ylim(*self.y_limits)

        cm_axis = secondary_axes[1]
        optimal_confusion_matrix = self.cms[self.optimal_index]
        disp = ConfusionMatrixDisplay(confusion_matrix=optimal_confusion_matrix)
        disp.plot(ax=cm_axis)

    def update_redis_trusted_values(self, node: str, this_element: str, transmon_parameters: list):
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
        REDIS_CONNECTION.hset(f"transmons:{this_element}", 'lda_coef_0', coef_0_)
        REDIS_CONNECTION.hset(f"transmons:{this_element}", 'lda_coef_1', coef_1_)
        REDIS_CONNECTION.hset(f"transmons:{this_element}", 'lda_intercept', intercept_)

        # We also update the values in the redis standard storage
        structured_redis_storage('lda_coef_0', this_element.strip('q'), coef_0_)
        structured_redis_storage('lda_coef_1', this_element.strip('q'), coef_1_)
        structured_redis_storage('lda_intercept', this_element.strip('q'), intercept_)


class OptimalRO_Three_state_AmplitudeAnalysis(OptimalROAmplitudeAnalysis):
    def __init__(self, dataset: xr.Dataset):
        self.dataset = dataset
        super().__init__(self.dataset)

    def run_fitting(self):
        self.run_initial_fitting()
        inv_cm_str = ",".join(str(element) for element in list(self.optimal_inv_cm.flatten()))

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
        iq_axis.scatter(self.IQ0_tp[:, 0], self.IQ0_tp[:, 1], marker=".", s=mark_size, color="red",
                        label='send 0 and read 0')
        iq_axis.scatter(self.IQ0_fp[:, 0], self.IQ0_fp[:, 1], marker="x", s=mark_size, color="orange", )
        iq_axis.scatter(self.IQ1_tp[:, 0], self.IQ1_tp[:, 1], marker=".", s=mark_size, color="blue",
                        label='send 1 and read 1')
        iq_axis.scatter(self.IQ1_fp[:, 0], self.IQ1_fp[:, 1], marker="x", s=mark_size, color="dodgerblue", )
        iq_axis.scatter(self.IQ2_tp[:, 0], self.IQ2_tp[:, 1], marker=".", s=mark_size, color="green")
        iq_axis.scatter(self.IQ2_fp[:, 0], self.IQ2_fp[:, 1], marker="x", s=mark_size, color="lime", )

        cm_axis = secondary_axes[1]
        optimal_confusion_matrix = self.cms[self.optimal_index]
        disp = ConfusionMatrixDisplay(confusion_matrix=optimal_confusion_matrix)
        disp.plot(ax=cm_axis)
