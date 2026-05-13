# This code is part of Tergite
#
# (c) Copyright Eleftherios Moschandreou 2024, 2025
# (c) Chalmers Next Labs 2024, 2025
#
# This code is licensed under the ache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import typing
from collections import namedtuple

import lmfit
import numpy as np
from lmfit.model import Model
from quantify_core.analysis.fitting_models import (exp_damp_osc_func,
                                                   fft_freq_phase_guess)
from scipy.ndimage import median
from scipy.optimize import minimize
from scipy.signal import find_peaks
from scipy.stats import median_abs_deviation
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

from tergite_autocalibration.lib.utils.functions import \
    exponential_decay_function


def resonator_hanger_frequency(
    *, fit_fr: float, fit_ph: float, fit_Qe: float, fit_Ql: float
) -> float:
    fit_Q = 4 * fit_Qe * fit_Ql
    resonator_frequency = (
        fit_fr
        / (fit_Q * np.sin(fit_ph))
        * (
            fit_Q * np.sin(fit_ph)
            - 2 * fit_Qe * np.cos(fit_ph)
            + fit_Ql
            + np.sqrt(4 * fit_Qe**2 - fit_Q * np.cos(fit_ph) + fit_Ql**2)
        )
    )
    return resonator_frequency


class ResonatorAvoidedCrossings:
    """
    Extract the avoided crossings from (currents, readout frequency) data.
    If the data have a shape like:

    ro_frequencies
    ^
    |           *             *
    |          *               *
    |   ******       ****        *********
    |              *      *
    |             *        *
    |________________________________> currents

    the crossings (intersection points X) of the frequency and current asymptotes are identified:
    ro_frequencies
    ^
    |            *|           | *
    |           * |           |  *
    |    ******   X    ****   X    *********
    |             |  *      * |
    |             | *        *|
    |_________________________________> currents
    """

    def __init__(self, currents, frequencies):
        self.currents = currents
        self.frequencies = frequencies

        self._analyze_crossings()

    def _analyze_crossings(self) -> None:
        frequency_diffs = np.diff(self.frequencies)
        noise_level = median_abs_deviation(frequency_diffs)
        peaks, _ = find_peaks(np.abs(frequency_diffs), prominence=10 * noise_level)
        self.jumps = peaks

    @property
    def crossing_currents(self) -> list[float]:
        crossing_currents = []
        for jump in self.jumps:
            current = np.mean((self.currents[jump], self.currents[jump + 1]))
            crossing_currents.append(current)
        return crossing_currents

    @property
    def crossing_frequency(self) -> float:
        return median(self.frequencies)

    @property
    def I0_hint(self) -> float | None:
        """
        hint for the current where the coupler has maximum frequency
        """
        if len(self.crossing_currents) != 2:
            return None
        return np.mean(self.crossing_currents)


class AvoidedCrossings:
    """
    Extract the avoided crossings from (currents, qubit frequency) data.
    This analysis utilizes only the geometric properties of the data, with no assumptions
    on the underlying physics of the coupler.
    If the data have a shape like:

    qubit
    frequencies
        ^
        | *     *           *     *
        | *     *           *     *
        |  *   *             *   *
        |    *                 *
        |            *
        |          *   *
        |         *     *
        _________________________________> currents

    the crossings (intersection points X) of the frequency and current asymptotes are identified:

    qubit
    frequencies
        ^*     * |       | *     *
        |*     * |       | *     *
        | *   *  |       |  *   *
        |   *    |       |    *
        |--------X-------X------------
        |        |   *   |
        |        | *   * |
        |        |*     *|
        _________________________________> currents
    """

    def __init__(self, currents, frequencies, threshold=2e6):
        self.currents = currents
        self.frequencies = frequencies
        self.threshold = threshold

        self._analyze_crossings()

    def _analyze_crossings(self) -> None:
        partition_indices = [0]

        currents = self.currents
        frequencies = self.frequencies

        frequency_diffs = np.diff(frequencies)
        (frequency_jumps,) = np.where(np.abs(frequency_diffs) > self.threshold)
        for jump in frequency_jumps:
            parity = self._parity_of_jump(jump, frequencies)
            if parity != (+1, -1, +1) and parity != (-1, +1, -1):
                continue

            # NOTE: to avoid confusion the index where the jump occurs in the currents array
            # is given a 0.5 offset to signal that is 'between' current samples.
            # this ends up being unnecessary and leads to having to cast to int when
            # asking for the low_sample and high_sample. It should be refactored.
            partition_indices.append(jump + 0.5)

        partition_indices.append(len(currents))
        self.partition_indices = partition_indices

    @classmethod
    def _parity_of_jump(cls, jump: int, frequencies: np.ndarray):
        frequency_diffs = np.diff(frequencies)
        sign_of_jump = np.sign(frequency_diffs[jump]).astype(int)
        if jump == 0:
            sign_before_jump = -sign_of_jump
        else:
            sign_before_jump = np.sign(frequency_diffs[jump - 1]).astype(int)
        if jump == len(frequency_diffs) - 1:
            # TODO: the logic is not solid here, may lead to errors
            sign_after_jump = -sign_of_jump
        else:
            sign_after_jump = np.sign(frequency_diffs[jump + 1]).astype(int)

        parity = (sign_before_jump, sign_of_jump, sign_after_jump)
        return parity

    @property
    def crossing_currents(self) -> list[float]:
        crossing_currents = []
        for current_boundary in self.partition_indices[1:-1]:
            low_sample = np.floor(current_boundary).astype(int)
            high_sample = np.ceil(current_boundary).astype(int)
            current = np.mean((self.currents[low_sample], self.currents[high_sample]))
            crossing_currents.append(current)
        return crossing_currents

    def _partition_samples(self):
        partitions_where_coupler_above_qubit = []
        partitions_where_coupler_below_qubit = []

        partition_boundaries = self.partition_indices
        crossing_partitions = [
            partition_boundaries[i : i + 2]
            for i in range(0, len(partition_boundaries) - 1)
        ]
        for partition in crossing_partitions:
            low_sample = np.ceil(partition[0]).astype(int)
            high_sample = np.floor(partition[1]).astype(int)
            partition_frequencies = self.frequencies[low_sample:high_sample]
            # small partitions may be misleading:
            if len(partition_frequencies) < 4:
                continue
            partition_frequencies_diffs = np.diff(partition_frequencies)

            # we use the slope of the frequency diffs to distinguish
            # the U-shaped partitions from the ∩-shaped partitions
            x = np.arange(len(partition_frequencies_diffs))
            slope, _ = np.polyfit(x, partition_frequencies_diffs, 1)
            if slope > 0:
                partitions_where_coupler_below_qubit.append(partition)
            elif slope < 0:
                partitions_where_coupler_above_qubit.append(partition)

        partitions = {
            "coupler_above_qubit": partitions_where_coupler_above_qubit,
            "coupler_below_qubit": partitions_where_coupler_below_qubit,
        }

        return partitions

    @property
    def crossing_frequency(self) -> typing.NamedTuple:
        partition_minima = []
        partition_maxima = []

        partitions = self._partition_samples()

        if len(partitions["coupler_above_qubit"]) == 1:
            (partition,) = partitions["coupler_above_qubit"]
            low_sample = np.ceil(partition[0]).astype(int)
            high_sample = np.floor(partition[1]).astype(int)
            low_current = self.currents[low_sample]
            high_current = self.currents[high_sample]
            self._coupler_hint = np.mean((low_current, high_current))
            if low_sample > 0 and high_sample < len(self.currents) - 1:
                self._delta_I_above = high_current - low_current
            else:
                self._delta_I_above = None
        else:
            self._delta_I_above = None
            self._coupler_hint = None

        if len(partitions["coupler_below_qubit"]) == 1:
            (partition,) = partitions["coupler_below_qubit"]
            low_sample = np.ceil(partition[0]).astype(int)
            high_sample = np.floor(partition[1]).astype(int)
            if low_sample > 0 and high_sample < len(self.currents) - 1:
                low_current = self.currents[low_sample]
                high_current = self.currents[high_sample]
                self._delta_I_below = high_current - low_current
            else:
                self._delta_I_below = None
        else:
            self._delta_I_below = None

        for partition in partitions["coupler_below_qubit"]:
            low_sample = np.ceil(partition[0]).astype(int)
            high_sample = np.floor(partition[1]).astype(int)
            partition_frequencies = self.frequencies[low_sample:high_sample]
            partition_minima.append(min(partition_frequencies))
        for partition in partitions["coupler_above_qubit"]:
            low_sample = np.ceil(partition[0]).astype(int)
            high_sample = np.floor(partition[1]).astype(int)
            partition_frequencies = self.frequencies[low_sample:high_sample]
            partition_maxima.append(max(partition_frequencies))

        if partition_minima:
            frequency_above = min(partition_minima)
        else:
            frequency_above = None
        if partition_maxima:
            frequency_below = max(partition_maxima)
        else:
            frequency_below = None
        if partition_minima and partition_maxima:
            cross_frequency = np.mean((frequency_above, frequency_below))
        else:
            cross_frequency = None

        frequency_values = namedtuple("cross_frequencies", ["value", "below", "above"])
        return frequency_values(
            value=cross_frequency, below=frequency_below, above=frequency_above
        )

    @property
    def Ic_hint(self) -> float | None:
        """
        hint for the current where the coupler has maximum frequency
        """
        return self._coupler_hint

    @property
    def I0_hint(self) -> float | None:
        """
        hint for the current corresponding to a quantum of magnetic flux
        """
        if self._delta_I_above and self._delta_I_below:
            return self._delta_I_below + self._delta_I_above


def coupler_frequency_function(
    current: float,
    fmax: float,
    Ic: float,
    I0: float,
    offset: float,
) -> float:
    '''
    the frequency of the coupler in terms of the applied bias current.
    Args:
    Ic: the current that gives maximum frequency
    I0: current corresponding to one quantum of flux
    '''
    return fmax * np.sqrt(np.abs(np.cos((current - Ic) / I0 * np.pi))) + offset


class CouplerModel(lmfit.model.Model):
    """
    Model for the coupler frequency of the form
    f = fmax*sqrt(abs(cos(pi * (I-Ic)/I0))) + offset
    """

    def __init__(self, *args, **kwargs):
        super().__init__(coupler_frequency_function, *args, **kwargs)

        # Typically couplers are designed up to 9GHz
        self.set_param_hint("fmax", value=9e9, min=6e9)
        # Expected current at fmax, helps the fitting algorithm
        self.set_param_hint("Ic", value=1e-3, vary=True)
        # Typically the period is around 3mAmp
        self.set_param_hint("I0", value=2.8e-3, vary=True)
        # Offset is a typical anharmonicity
        self.set_param_hint("offset", value=0, max=300e6)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        current = kws.get("current", None)
        if current is None:
            raise ValueError(
                'Variable "current" must be specified in order to guess parameters'
            )

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)



class CouplingModel():
    """
    Model to find the coupling strength g between a tunable transmon and a 
    fixed frequency transmon.
    """
    def __init__(self,fixed_qubit_frequency:float , coupler_model: lmfit.model.ModelResult, data_dc_currents, data_frequencies):
        self.fixed_qubit_frequency = fixed_qubit_frequency
        self.coupler_model = coupler_model
        self.data_dc_currents = data_dc_currents
        self.data_frequencies = data_frequencies

    def model_data(self, g):
        omega_q = self.fixed_qubit_frequency
        dc_currents = self.data_dc_currents
        coupler_omegas = self.coupler_model.eval(
            self.coupler_model.params, current=self.data_dc_currents
        )
        anal_freq_plus = (omega_q + coupler_omegas) / 2 + np.sqrt(
            ((omega_q - coupler_omegas) / 2) ** 2 + g**2
        )
        anal_freq_minus = (omega_q + coupler_omegas) / 2 - np.sqrt(
            ((omega_q - coupler_omegas) / 2) ** 2 + g**2
        )
        deltas = omega_q - coupler_omegas
        thetas = np.arctan(2 * g / deltas) / 2
        qubit_positions_plus = np.logical_and(np.cos(thetas) ** 2 > 0.99, deltas > 0)
        qubit_positions_minus = np.logical_and(np.cos(thetas) ** 2 > 0.99, deltas < 0)
        qubit_freqs_plus = anal_freq_plus[qubit_positions_plus]
        dc_currents_plus = dc_currents[qubit_positions_plus]
        qubit_freqs_minus = anal_freq_minus[qubit_positions_minus]
        dc_currents_minus = dc_currents[qubit_positions_minus]

        valid_positions = np.logical_or(qubit_positions_plus , qubit_positions_minus)
        valid_data_frequencies = self.data_frequencies[valid_positions]

        plus_values = list(zip(dc_currents_plus, qubit_freqs_plus))
        minus_values = list(zip(dc_currents_minus, qubit_freqs_minus))

        values = plus_values + minus_values
        sorted_values = sorted(values, key=lambda tup: tup[0])
        sorted_dc_currents, sorted_frequencies = zip(*sorted_values)
        return sorted_dc_currents, sorted_frequencies, valid_data_frequencies

    def cost_function(self, g: float):
        _, model_frequencies, data_frequencies = self.model_data(g)
        # TODO: some of them are xarray datarrays
        norm = np.sum(np.abs(data_frequencies - model_frequencies))
        return norm

    @property
    def coupling_g(self):
        return minimize(self.cost_function, x0=50e6, method='Nelder-Mead')


def straighten_ramsey_points(artificial_detunings: np.ndarray, fitted_detunings: np.ndarray) -> np.ndarray:
    '''
    for data corresponding to fitted vs artificial detunings:
    * | 
      |             *
      | *
      |         *
      |      *
      |------------------------->
      |

      we find the inflection point and multiply the data before the inflection point by -1
      in order to form a line
      | 
      |             *
      |  
      |         *
      |      *
      |------------------------->
      |  
      |  * 
      |  
      |  
    * |  
    '''
    complex_points = artificial_detunings + 1j * fitted_detunings
    directions = np.diff(complex_points)
    angles_of_diffs = np.angle(directions)
    sins_of_diffs = np.abs(np.sin(angles_of_diffs))
    index_of_min = np.argmin(sins_of_diffs) + 1
    linear_fitted_detunings = np.concatenate(
        (fitted_detunings[:index_of_min] * (-1), fitted_detunings[index_of_min:])
    )
    return linear_fitted_detunings

class RamseyModel(lmfit.model.Model):
    """
    Model for exponentially decaying sinusoidal data of the form
    amplitude*exp(-tau * t)*sin(frequency * t + phase) + offset
    tau is the characteristic decay constant and omega the frequency of the measured Ramsey Oscillations.
    The data are collected over a sequence of Ramsey delays t, i.e. delays between two consecutive X90 gates.
    Used by measurements that calibrate or characterize qubit dephasing:
    Ramsey correction, T2, T2echo
    """

    def __init__(self, *args, **kwargs):
        # pass in the defining equation so the user doesn't have to later.
        super().__init__(exp_damp_osc_func, *args, **kwargs)

        # Enforce oscillation frequency is positive
        self.set_param_hint("frequency", min=0)
        # Enforce amplitude is positive
        self.set_param_hint("amplitude", min=0)
        # Enforce decay time is positive
        self.set_param_hint("tau", min=0)

        # Fix the n_factor at 1
        self.set_param_hint("n_factor", expr="1", vary=False)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        t = kws.get("t", None)
        if t is None:
            raise ValueError(
                'Time variable "t" must be specified in order to guess parameters'
            )

        amp_guess = abs(max(data) - min(data)) / 2  # amp is positive by convention
        exp_offs_guess = np.mean(data)
        tau_guess = 2 / 3 * np.max(t)

        freq_guess, phase_guess = fft_freq_phase_guess(data, t)

        self.set_param_hint("frequency", value=freq_guess, min=0)
        self.set_param_hint("amplitude", value=amp_guess, min=0)
        self.set_param_hint("offset", value=exp_offs_guess)
        self.set_param_hint("phase", value=phase_guess)
        self.set_param_hint("tau", value=tau_guess, min=0)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


# Cosine function that is fit to Rabi oscillations
def cos_func(
    drive_amp: float,
    frequency: float,
    amplitude: float,
    offset: float,
    phase: float,
) -> float:
    return amplitude * np.cos(2 * np.pi * frequency * drive_amp + phase) + offset


class RabiModel(lmfit.model.Model):
    """
    Generate a cosine model that can be fit to Rabi oscillation data.
    """

    def __init__(self, *args, **kwargs):
        # Pass in the defining equation so the user doesn't have to later.
        super().__init__(cos_func, *args, **kwargs)

        # Enforce oscillation frequency is positive
        self.set_param_hint("frequency", min=0)

        # Fix the phase at pi so that the ouput is at a minimum when drive_amp=0
        self.set_param_hint("phase", expr="3.141592653589793", vary=True)

        # Pi-pulse amplitude can be derived from the oscillation frequency
        self.set_param_hint("amp180", expr="1/(2*frequency)", vary=False)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        drive_amp = kws.get("drive_amp", None)
        if drive_amp is None:
            return None

        amp_guess = abs(max(data) - min(data)) / 2  # amp is positive by convention
        offs_guess = np.mean(data)

        # Frequency guess is obtained using a fast fourier transform (FFT).
        freq_guess, _ = fft_freq_phase_guess(data, drive_amp)

        self.set_param_hint("frequency", value=freq_guess, min=0)
        self.set_param_hint("amplitude", value=amp_guess, min=0)
        self.set_param_hint("offset", value=offs_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


def sin_func(
    x: float,
    frequency: float,
    amplitude: float,
    offset: float,
    phase: float = 0,
) -> float:
    return amplitude * np.cos(2 * np.pi * frequency * x + phase) + offset


class TwoClassBoundary:
    """
    Converts the boundary encoded in the LDA discriminator.
    The LDA boundary (also called threshold) has the form Ax + By + y_intercept = 0.
    This boundary is converted:
    i. To the form y = lamda * x + y_intercept, used in plotting
    ii. To the form (theta, threshold) used by the Quantify Scheduler for Thresholded Aqcuisitions

    Attributes
    ----------
    lamda: float
        the slope coefficient of form (i)
    y_intercept: float
        the y-axis intercept of form (i)
    theta_rad: float
        the angle of the boundary, used for form (ii)
    threshold: float
        the distance from the IQ origin to the boundary line, used for form (ii)
    """

    def __init__(self, lda: LinearDiscriminantAnalysis):
        if len(lda.classes_) != 2:
            raise ValueError("The Classifcation classes are not 2.")
        # determining the discriminant line from the canonical form Ax + By + intercept = 0
        A = lda.coef_[0][0]
        B = lda.coef_[0][1]
        self.centers = lda.means_
        intercept = lda.intercept_
        self.lamda = -A / B
        self.theta_rad = np.arctan(self.lamda)
        threshold = np.abs(intercept) / np.sqrt(A**2 + B**2)
        self.threshold = threshold[0]
        self.y_intercept = -intercept / B


class ThreeClassBoundary:
    """
    Defines the classification boundaries when discriminating between
    the |0>, |1>, |2> qubit states.
    Such definition requires 5 parameters:
    the (I,Q) coordinates of the point where the three lines meet (centroid)
    the angles omega_ij that define the direction of each line with respect to the I axis

    Attributes
    ----------
    centroid_I: float
        the I coordinate of the point where the three classification lines meet
    centroid_Q: float
        the Q coordinate of the point where the three classification lines meet
    omega_01: float
        the angle in degrees in the range [0,360) of the boundary between |0> and |1>
    omega_12: float
        the angle in degrees in the range [0,360) of the boundary between |1> and |2>
    omega_20: float
        the angle in degrees in the range [0,360) of the boundary between |2> and |0>

    Methods
    ----------
    boundary_line (int: class_a, class_a) -> (np.ndarray, np.ndarray):
        used for plotting,
        returns the x and y points needed to plot
        the line between the classes class_a and class_b. The line starts at the centroid.
    """

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

    def boundary_line(
        self, class_a: int, class_b: int
    ) -> tuple[np.ndarray, np.ndarray]:
        i_point = self.intersection_I(class_a, class_b)
        q_point = self.intersection_Q(class_a, class_b)
        i_values = np.linspace(self.centroid[0], i_point, 100)
        boundary_slope = (q_point - self.centroid[1]) / (i_point - self.centroid[0])
        return (
            i_values,
            boundary_slope * (i_values - self.centroid[0]) + self.centroid[1],
        )


class ExpDecayModel(lmfit.model.Model):
    """
    Generate an exponential decay model that can be fit to randomized benchmarking data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(exponential_decay_function, *args, **kwargs)

        self.set_param_hint("A", vary=True)
        self.set_param_hint("B", vary=True, min=0)
        self.set_param_hint("p", vary=True, min=0)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        m = kws.get("m", None)

        if m is None:
            return None

        amplitude_guess = 1 / 2
        self.set_param_hint("A", value=amplitude_guess)

        offset_guess = data[-1]
        self.set_param_hint("B", value=offset_guess)

        p_guess = 0.95
        self.set_param_hint("p", value=p_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


def sin_func(
    x: float,
    frequency: float,
    amplitude: float,
    offset: float,
    phase: float = 0,
) -> float:
    return amplitude * np.cos(2 * np.pi * frequency * x + phase) + offset


class SineOscillatingModel(lmfit.model.Model):
    def __init__(self, *args, **kwargs):
        # pass in the defining equation so the user doesn't have to later.
        super().__init__(sin_func, *args, **kwargs)

        # Enforce oscillation frequency is positive
        self.set_param_hint("frequency", min=0)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        independent_values = kws.get("x")

        amp_guess = abs(max(data) - min(data)) / 2  # amp is positive by convention
        offs_guess = np.mean(data)

        freq_guess, _ = fft_freq_phase_guess(data, independent_values)

        self.set_param_hint("frequency", value=freq_guess, min=freq_guess * 0.8)
        self.set_param_hint("amplitude", value=amp_guess, min=amp_guess * 0.8)
        self.set_param_hint("offset", value=offs_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


def chevron_func(x, x0, amplitude, curvature, offset):
    return -np.sqrt(amplitude * (x - x0) ** 2 + curvature) + offset


# def chevron_func(x, x0, amplitude, offset):
#     return -amplitude * np.sqrt((x - x0) ** 2) + offset


class CzChevronModel(lmfit.model.Model):
    def __init__(self, *args, **kwargs):
        # pass in the defining equation so the user doesn't have to later.
        super().__init__(chevron_func, *args, **kwargs)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:

        amp_guess = 1e6
        offs_guess = np.max(data)
        curvature_guess = 1

        self.set_param_hint("curvature", value=curvature_guess, min=0)
        self.set_param_hint("offset", value=offs_guess, min=0)
        self.set_param_hint("amplitude", value=amp_guess, min=0)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


def parabolic(x, x0=0, a=0.0, c=0.0):
    """Return a parabolic function.

    parabolic(x, x0, a, c) = a * (x-x0)**2  + c

    """
    return a * (x - x0) ** 2 + c


class QuadraticModel(Model):
    """A quadratic model, with three Parameters: `x0`, `a`, and `c`.

    Defined as:

    .. math::

        f(x; x0, a, c) =  a * (x-x0)**2  + c

    """

    def __init__(self, independent_vars=["x"], prefix="", nan_policy="raise", **kwargs):
        kwargs.update(
            {
                "prefix": prefix,
                "nan_policy": nan_policy,
                "independent_vars": independent_vars,
            }
        )
        super().__init__(parabolic, **kwargs)

    def guess(self, data, x, **kwargs):
        """Estimate initial model parameter values from data."""
        c_guess = np.max(data)
        index_max_duration = np.argmax(data)
        freq_at_max_duration = x[index_max_duration]

        # guess a: assume that a x-x0 = 2MHz -> y-y0 = - 12ns
        a_guess = -12e-9 / (2e6) ** 2

        pars = self.make_params(x0=freq_at_max_duration, a=a_guess, c=c_guess)
        self.set_param_hint("x0", min=x.min(), max=x.max())
        return lmfit.models.update_param_vals(pars, self.prefix, **kwargs)
