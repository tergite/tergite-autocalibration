# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import lmfit
import numpy as np
from matplotlib.axes import Axes

from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.lib.utils.functions import (
    exponential_decay_function,
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


class RandomizedBenchmarkingQubitAnalysis(BaseQubitAnalysis):
    """
    Analysis that fits an exponential decay function to randomized benchmarking data.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}

    def analyse_qubit(self):
        for coord in self.dataset[self.data_var].coords:
            if "cliffords" in coord:
                self.number_cliffords_coord = coord
            elif "seed" in coord:
                self.seed_coord = coord

        self.number_of_repetitions = self.dataset.dims[self.seed_coord]
        self.number_of_cliffords = self.dataset[self.number_cliffords_coord].values
        self.number_of_cliffords_runs = (
            self.dataset.dims[self.number_cliffords_coord] - 3
        )
        self.normalized_data_dict = {}

        for repetition_index in range(self.number_of_repetitions):
            magnitudes_flat = self._get_magnitudes(repetition_index)

            data = magnitudes_flat[:-3]
            calibration_0 = magnitudes_flat[-3]
            calibration_1 = magnitudes_flat[-2]
            calibration_2 = magnitudes_flat[-1]
            # print('these are the zero and one points respectively: ', calibration_0, calibration_1)
            # print('these are the unrotated data points: ', data)
            displacement_vector = calibration_1 - calibration_0
            data_translated_to_zero = data - calibration_0

            rotation_angle = np.angle(displacement_vector)
            rotated_data = data_translated_to_zero * np.exp(-1j * rotation_angle)
            rotated_0 = calibration_0 * np.exp(-1j * rotation_angle)
            rotated_1 = calibration_1 * np.exp(-1j * rotation_angle)
            rotated_2 = calibration_2 * np.exp(-1j * rotation_angle)
            normalization = (rotated_1 - rotated_0).real
            real_rotated_data = rotated_data.real
            self.normalized_data_dict[repetition_index] = (
                real_rotated_data / normalization
            )

        sum = np.sum([arr for arr in self.normalized_data_dict.values()], axis=0)
        self.sum = sum / len(self.normalized_data_dict)

        model = ExpDecayModel()

        n_cliffords = self.number_of_cliffords[:-3]

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(data=self.sum, m=n_cliffords)
        fit_result = model.fit(self.sum, params=guess, m=n_cliffords)

        self.fit_n_cliffords = np.linspace(n_cliffords[0], n_cliffords[-1], 400)
        self.fit_y = model.eval(
            fit_result.params, **{model.independent_vars[0]: self.fit_n_cliffords}
        )
        self.fidelity = fit_result.params["p"].value
        return [self.fidelity]

    def _get_magnitudes(self, indx):
        magnitudes = self.S21[self.data_var].isel({self.seed_coord: indx})
        return magnitudes.values.flatten()

    def plotter(self, ax: Axes):
        for repetition_index in range(self.number_of_repetitions):
            real_values = self.normalized_data_dict[repetition_index]
            ax.plot(self.number_of_cliffords[:-3], real_values, alpha=0.2)
            ax.annotate(
                f"{repetition_index}",
                (self.number_of_cliffords[:-3][-1], real_values[-1]),
            )

        ax.plot(
            self.fit_n_cliffords,
            self.fit_y,
            "ro-",
            lw=2.5,
            label=f"p = {self.fidelity:.3f}",
        )
        ax.plot(self.number_of_cliffords[:-3], self.sum, ls="dashed", c="black")
        ax.set_ylabel(f"|S21| (V)")
        ax.grid()


class RandomizedBenchmarkingNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = RandomizedBenchmarkingQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.repeat_coordinate_name = "seeds"
