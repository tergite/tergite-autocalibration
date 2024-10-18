# This code is part of Tergite
#
# (C) Copyright Joel Sandås 2024
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
Module containing classes that model, fit and plot data from the purity benchmarking experiment.
"""
import lmfit
from matplotlib.axes import Axes
import numpy as np

from ....base.analysis import BaseAllQubitsRepeatAnalysis, BaseQubitAnalysis
from ....utils.functions import exponential_decay_function


class ExpDecayModel(lmfit.model.Model):
    """
    Generate an exponential decay model that can be fit to purity benchmarking data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(exponential_decay_function, *args, **kwargs)

        # Set parameter hints for the fitting process
        self.set_param_hint("A", vary=True)
        self.set_param_hint("B", vary=True, min=0)
        self.set_param_hint("p", vary=True, min=0)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        """
        Generate initial guesses for the model parameters based on the data.
        """
        m = kws.get("m", None)
        if m is None:
            return None

        # Initial guesses
        amplitude_guess = data[0]
        offset_guess = data[-4]
        p_guess = 0.95

        self.set_param_hint("A", value=amplitude_guess)
        self.set_param_hint("B", value=offset_guess)
        self.set_param_hint("p", value=p_guess)

        # Create and return the parameters object with initial guesses
        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


class PurityBenchmarkingQubitAnalysis(BaseQubitAnalysis):
    """
    Analysis that fits an exponential decay function to purity benchmarking data.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}

    def analyse_qubit(self):
        # Identify and store relevant coordinates and initialize data storage
        self.number_cliffords_coord, self.seed_coord = self._identify_coords()
        self.number_of_repetitions = self.dataset.sizes[self.seed_coord]
        self.number_of_cliffords = np.unique(
            self.dataset[self.number_cliffords_coord].values[:-3]
        )

        self.normalized_data_dict = {}
        self.purity_results_dict = {}
        self.fit_n_cliffords, self.fit_y, self.fidelity, self.fit_report = (
            None,
            None,
            None,
            None,
        )

        # Process and normalize the purity data
        self._process_and_normalize_data()
        return self._fit_data()

    def _identify_coords(self):
        """
        Identify the coordinates related to the number of Cliffords and seed.
        """
        number_cliffords_coord = None
        seed_coord = None

        for coord in self.dataset.coords:
            if "cliffords" in coord:
                number_cliffords_coord = coord
            elif "seed" in coord:
                seed_coord = coord

        return number_cliffords_coord, seed_coord

    def _process_and_normalize_data(self):
        """
        Process and normalize purity data for each repetition, and calculate the purity per index.
        """
        for repetition_index in range(self.number_of_repetitions):
            measurements = self._get_magnitudes(repetition_index)
            data = measurements[:-3]  # Data excluding calibration points
            calibration_0, calibration_1 = measurements[-3], measurements[-2]

            # Normalize and rotate data
            displacement_vector = calibration_1 - calibration_0
            data_translated_to_zero = data - calibration_0

            rotation_angle = np.angle(displacement_vector)
            rotated_data = data_translated_to_zero * np.exp(-1j * rotation_angle)
            rotated_0 = calibration_0 * np.exp(-1j * rotation_angle)
            rotated_1 = calibration_1 * np.exp(-1j * rotation_angle)
            normalization = (rotated_1 - rotated_0).real
            normalized_data = rotated_data.real / normalization

            # Calculate purity for each acquisition index
            purity_per_index = []
            for i in range(len(normalized_data) // 3):
                # Extract values for the Pauli operators
                x_1, y_1, z_1 = normalized_data[3 * i: 3 * (i + 1)]
                x_exp = 2 * x_1 - 1
                y_exp = 2 * y_1 - 1
                z_exp = 2 * z_1 - 1

                # Calculate purity
                purity_per_index.append(x_exp ** 2 + y_exp ** 2 + z_exp ** 2)

            # Store normalized data and purity results
            self.normalized_data_dict[repetition_index] = normalized_data
            self.purity_results_dict[repetition_index] = purity_per_index

    def _get_magnitudes(self, indx):
        magnitudes = self.S21[self.data_var].isel({self.seed_coord: indx})
        return magnitudes.values.flatten()

    def _fit_data(self):
        """
        Fit the exponential decay model to the averaged purity data.
        """
        # Calculate the average purity across all repetitions
        sum_purity = np.sum(list(self.purity_results_dict.values()), axis=0)
        avg_purity = sum_purity / len(self.purity_results_dict)

        sum = np.sum([arr for arr in self.normalized_data_dict.values()], axis=0)
        self.sum = sum / len(self.normalized_data_dict)

        print(self.sum)
        print(avg_purity)

        # Initialize the exponential decay model
        model = ExpDecayModel()
        n_cliffords = np.array(self.number_of_cliffords)

        # Generate initial parameter guesses and fit the model to the data
        guess = model.guess(data=avg_purity, m=n_cliffords)
        fit_result = model.fit(avg_purity, params=guess, m=n_cliffords)

        # Generate fitted values for plotting
        self.fit_n_cliffords = np.linspace(n_cliffords[0], n_cliffords[-1], 400)
        self.fit_y = model.eval(fit_result.params, m=self.fit_n_cliffords)
        self.fidelity = fit_result.params["p"].value

        # Store fit results and report
        self.fit_results = fit_result
        self.fit_report = fit_result.fit_report()
        print(self.fit_report)

        return [self.fidelity]

    def plotter(self, ax: Axes):
        """
        Plot the normalized data and fitted exponential decay curve.
        """
        # Plot normalized data for each repetition with low transparency
        for repetition_index, real_values in self.purity_results_dict.items():
            ax.plot(self.number_of_cliffords, real_values, alpha=0.2)
            ax.annotate(
                f"{repetition_index}", (self.number_of_cliffords[-1], real_values[-1])
            )

        # Plot the fitted curve and add labels
        ax.plot(
            self.fit_n_cliffords,
            self.fit_y,
            "ro-",
            lw=2.5,
            label=f"p = {self.fidelity:.3f}",
        )
        ax.plot(
            self.number_of_cliffords,
            self.fit_results.best_fit,
            ls="dashed",
            color="black",
        )
        ax.set_ylabel("Purity")
        ax.set_xlabel("Number of Cliffords")
        ax.grid()


class PurityBenchmarkingNodeAnalysis(BaseAllQubitsRepeatAnalysis):
    single_qubit_analysis_obj = PurityBenchmarkingQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.repeat_coordinate_name = "seeds"
