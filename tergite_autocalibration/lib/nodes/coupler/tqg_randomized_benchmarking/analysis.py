# This code is part of Tergite
#
# (C) Copyright Amr Osman 2024
# (C) Copyright Eleftherios Moschandreou 2025, 2026
# (C) Copyright Chalmers Next Labs 2025, 2026
# (C) Copyright Pontus Vikstål 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from tergite_autocalibration.lib.base.analysis import (
    BaseAllCouplersAnalysis,
    BaseCouplerAnalysis,
)
from tergite_autocalibration.lib.utils.analysis_models import ExpDecayModel
from tergite_autocalibration.lib.utils.classification_functions import (
    calculate_probabilities,
)
from tergite_autocalibration.utils.dto.qoi import QOI


class TwoQubitRnBAnalysis(BaseCouplerAnalysis):

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.single_model = ExpDecayModel(inverted=False)

    def state_probabilities(self, c_qubit_state: int, t_qubit_state: int):
        c_state_probs = self.control_qubit_probabilities.sel({"state": c_qubit_state})
        t_state_probs = self.target_qubit_probabilities.sel({"state": t_qubit_state})
        return c_state_probs * t_state_probs

    def analyze_coupler(self):

        computational_space_dimension = 4

        dataset = self.S21
        for coord in dataset.coords:
            coord = str(coord)
            if "cliffords" in coord:
                self.number_cliffords_coord = coord
                self.number_cliffords = self.S21[coord].values
            elif "seed" in coord:
                self.seed_coord = coord
                self.seeds = self.S21[coord].values
            elif "loops" in coord:
                self.loops_coord = coord
                self.number_of_loops = self.S21[coord].size
            elif "interleave" in coord:
                self.interleave_modes_coord = coord
                self.interleave_modes = self.S21[coord].values
                self.number_of_modes = self.S21[coord].size
            else:
                raise ValueError

        self.control_qubit_probabilities = calculate_probabilities(
            self.control_qubit_data_var
        )
        self.target_qubit_probabilities = calculate_probabilities(
            self.target_qubit_data_var
        )

        number_cliffords = self.number_cliffords

        self.P00 = self.state_probabilities(0, 0)
        self.P01 = self.state_probabilities(0, 1)
        self.P10 = self.state_probabilities(1, 0)
        self.P11 = self.state_probabilities(1, 1)
        self.P02 = self.state_probabilities(0, 2)
        self.P12 = self.state_probabilities(1, 2)
        self.P20 = self.state_probabilities(2, 0)
        self.P21 = self.state_probabilities(2, 1)
        self.P22 = self.state_probabilities(2, 2)

        mean_probabilities_00 = self.P00.mean(self.seed_coord)
        mean_probabilities_01 = self.P01.mean(self.seed_coord)
        mean_probabilities_10 = self.P10.mean(self.seed_coord)
        mean_probabilities_11 = self.P11.mean(self.seed_coord)
        mean_probabilities_02 = self.P02.mean(self.seed_coord)
        mean_probabilities_20 = self.P20.mean(self.seed_coord)
        mean_probabilities_21 = self.P21.mean(self.seed_coord)
        mean_probabilities_12 = self.P12.mean(self.seed_coord)
        mean_probabilities_22 = self.P22.mean(self.seed_coord)

        # probabilities to of states in the computational subspace
        mean_probabilities_chi_1 = (
            mean_probabilities_00
            + mean_probabilities_01
            + mean_probabilities_10
            + mean_probabilities_11
        )

        standard_mean_probs_00 = mean_probabilities_00.sel(
            {self.interleave_modes_coord: False}
        )

        standard_mean_probs_chi_1 = mean_probabilities_chi_1.sel(
            {self.interleave_modes_coord: False}
        )

        standard_reduced_ideal_probabilities = (
            standard_mean_probs_00
            - standard_mean_probs_chi_1 / computational_space_dimension
        )
        interleaved_mean_probs_00 = mean_probabilities_00.sel(
            {self.interleave_modes_coord: True}
        )

        interleaved_mean_probs_chi_1 = mean_probabilities_chi_1.sel(
            {self.interleave_modes_coord: True}
        )
        interleaved_reduced_ideal_probabilities = (
            interleaved_mean_probs_00
            - interleaved_mean_probs_chi_1 / computational_space_dimension
        )

        ## Calculate the CZ Fidelity based on Nakamura's paper
        # Fit 1: fit probabilities of the computational states eq. K14
        standard_guess_Pchi_1 = self.single_model.guess(
            data=standard_mean_probs_chi_1.values, m=number_cliffords
        )

        standard_fit_Pchi_1_result = self.single_model.fit(
            standard_mean_probs_chi_1.values,
            params=standard_guess_Pchi_1,
            m=number_cliffords,
        )

        # Fit 2: fit the reduced ideal probabilities eq. K15
        standard_guess_Pideal = self.single_model.guess(
            data=standard_reduced_ideal_probabilities.values,
            m=number_cliffords,
        )

        standard_fit_Pideal_result = self.single_model.fit(
            standard_reduced_ideal_probabilities.values,
            params=standard_guess_Pideal,
            m=number_cliffords,
        )
        ##################################################

        standard_guess = self.single_model.guess(
            data=standard_mean_probs_00.values, m=number_cliffords
        )
        standard_fit_result = self.single_model.fit(
            standard_mean_probs_00.values,
            params=standard_guess,
            m=number_cliffords,
        )

        self.fit_n_cliffords = np.linspace(
            number_cliffords[0], number_cliffords[-1], 200
        )
        self.standard_fit_y = self.single_model.eval(
            standard_fit_result.params, **{"m": self.fit_n_cliffords}
        )
        self.standard_fit_Pchi_1_y = self.single_model.eval(
            standard_fit_Pchi_1_result.params, **{"m": self.fit_n_cliffords}
        )
        self.standard_fit_Pideal_y = self.single_model.eval(
            standard_fit_Pideal_result.params, **{"m": self.fit_n_cliffords}
        )
        if True in self.interleave_modes:
            interleaved_mean_probs_00 = mean_probabilities_00.sel(
                {self.interleave_modes_coord: True}
            )
            interleaved_mean_probs_chi_1 = mean_probabilities_chi_1.sel(
                {self.interleave_modes_coord: True}
            )
            interleaved_guess = self.single_model.guess(
                data=interleaved_mean_probs_00.values,
                m=number_cliffords,
            )
            interleaved_fit_result = self.single_model.fit(
                interleaved_mean_probs_00.values,
                params=interleaved_guess,
                m=number_cliffords,
            )
            interleaved_guess_Pchi_1 = self.single_model.guess(
                data=interleaved_mean_probs_chi_1.values,
                m=number_cliffords,
            )

            interleaved_fit_Pchi_1_result = self.single_model.fit(
                interleaved_mean_probs_chi_1.values,
                params=interleaved_guess_Pchi_1,
                m=number_cliffords,
            )
            interleaved_guess_Pideal = self.single_model.guess(
                data=interleaved_reduced_ideal_probabilities.values,
                m=number_cliffords,
            )

            interleaved_fit_Pideal_result = self.single_model.fit(
                interleaved_reduced_ideal_probabilities.values,
                params=interleaved_guess_Pideal,
                m=number_cliffords,
            )
            self.interleaved_fit_Pideal_y = self.single_model.eval(
                interleaved_fit_Pideal_result.params, **{"m": self.fit_n_cliffords}
            )
            self.interleaved_fit_Pchi_1_y = self.single_model.eval(
                interleaved_fit_Pchi_1_result.params, **{"m": self.fit_n_cliffords}
            )
            self.interleaved_fit_y = self.single_model.eval(
                interleaved_fit_result.params, **{"m": self.fit_n_cliffords}
            )
            self.interleaved_p = interleaved_fit_result.params["p"].value
            self.interleaved_lambda_L = interleaved_fit_Pchi_1_result.params["p"].value
            self.interleaved_AM = interleaved_fit_Pchi_1_result.params["A"].value
            self.interleaved_BM = interleaved_fit_Pchi_1_result.params["B"].value
            self.interleaved_lambda_r = interleaved_fit_Pideal_result.params["p"].value
            self.interleaved_p = interleaved_fit_result.params["p"].value

        self.standard_p = standard_fit_result.params["p"].value
        self.standard_lambda_L = standard_fit_Pchi_1_result.params["p"].value
        self.standard_AM = standard_fit_Pchi_1_result.params["A"].value
        self.standard_BM = standard_fit_Pchi_1_result.params["B"].value
        self.standard_lambda_r = standard_fit_Pideal_result.params["p"].value

        L1_standard = (1 - self.standard_lambda_L) * (1 - self.standard_AM)
        L2_standard = (1 - self.standard_lambda_L) * self.standard_AM
        L1_interleaved = (1 - self.interleaved_lambda_L) * (1 - self.interleaved_AM)
        L2_interleaved = (1 - self.interleaved_lambda_L) * self.interleaved_AM
        self.one_minus_L1_CZ = (1 - L1_interleaved) / (1 - L1_standard)
        self.lambda_r_CZ = self.interleaved_lambda_r / self.standard_lambda_r

        # Fidelity based on Nakamura's paper
        self.average_fidelity = 3 / 4 * self.lambda_r_CZ + self.one_minus_L1_CZ / 4

        analysis_succesful = False
        analysis_result = {
            "cz_fidelity": {
                "value": 0,
                "error": 0,
            },
        }
        qoi = QOI(analysis_result, analysis_succesful)
        return qoi

    @property
    def processed_dataset(self):
        self.probabilities = xr.concat(
            [self.control_qubit_probabilities, self.target_qubit_probabilities],
            dim="qubit",
        )
        return self.probabilities

    def plotter(self, figures_dictionary):

        fig, axs = plt.subplots(ncols=2)

        computational_space_dimension = 4

        standard_probs_00 = self.P00.sel({self.interleave_modes_coord: False})
        standard_probs_chi_1 = (self.P00 + self.P01 + self.P10 + self.P11).sel(
            {self.interleave_modes_coord: False}
        )
        standard_probs_reduced_ideal = (
            standard_probs_00 - standard_probs_chi_1 / computational_space_dimension
        )
        interleaved_probs_00 = self.P00.sel({self.interleave_modes_coord: False})
        interleaved_probs_chi_1 = (self.P00 + self.P01 + self.P10 + self.P11).sel(
            {self.interleave_modes_coord: False}
        )
        interleaved_probs_reduced_ideal = (
            interleaved_probs_00
            - interleaved_probs_chi_1 / computational_space_dimension
        )
        standard_probs_00.plot(
            ax=axs[0], x=self.number_cliffords_coord, hue=self.seed_coord, alpha=0.2
        )
        standard_probs_chi_1.plot(
            ax=axs[1], x=self.number_cliffords_coord, hue=self.seed_coord, alpha=0.2
        )
        standard_probs_reduced_ideal.plot(
            ax=axs[1], x=self.number_cliffords_coord, hue=self.seed_coord, alpha=0.2
        )
        interleaved_probs_chi_1.plot(
            ax=axs[1], x=self.number_cliffords_coord, hue=self.seed_coord, alpha=0.2
        )
        interleaved_probs_reduced_ideal.plot(
            ax=axs[1], x=self.number_cliffords_coord, hue=self.seed_coord, alpha=0.2
        )
        axs[0].plot(
            self.fit_n_cliffords,
            self.standard_fit_y,
            color="red",
            lw=3,
            label=rf"$p_{{SRB}}$: {self.standard_p:.3f}",
        )
        lambda_standard_str = rf"$\lambda_L^{{SRB}}$: {self.standard_lambda_L:.3f}"
        A_standard_str = rf"$A_M^{{SRB}}$: {self.standard_AM:.3f}"
        L1_standard = (1 - self.standard_lambda_L) * (1 - self.standard_AM)
        L2_standard = (1 - self.standard_lambda_L) * self.standard_AM
        L1_standard_str = rf"$L1^{{SRB}}$: {L1_standard:.3f}"
        L2_standard_str = rf"$L2^{{SRB}}$: {L2_standard:.3f}"
        standard_label = (
            lambda_standard_str
            + " "
            + A_standard_str
            + "\n"
            + L1_standard_str
            + " "
            + L2_standard_str,
        )
        lambda_interleaved_str = (
            rf"$\lambda_L^{{IRB}}$: {self.interleaved_lambda_L:.3f}"
        )
        A_interleaved_str = rf"$A_M^{{IRB}}$: {self.interleaved_AM:.3f}"
        L1_interleaved = (1 - self.interleaved_lambda_L) * (1 - self.interleaved_AM)
        L2_interleaved = (1 - self.interleaved_lambda_L) * self.interleaved_AM
        L1_interleaved_str = rf"$L1^{{IRB}}$: {L1_interleaved:.3f}"
        L2_interleaved_str = rf"$L2^{{IRB}}$: {L2_interleaved:.3f}"
        interleaved_label = (
            lambda_interleaved_str
            + " "
            + A_interleaved_str
            + "\n"
            + L1_interleaved_str
            + " "
            + L2_interleaved_str,
        )

        axs[1].plot(
            self.fit_n_cliffords,
            self.standard_fit_Pchi_1_y,
            color="teal",
            lw=3,
            label=standard_label,
        )
        axs[1].plot(
            self.fit_n_cliffords,
            self.interleaved_fit_Pchi_1_y,
            color="orange",
            lw=3,
            label=interleaved_label,
        )
        axs[1].plot(
            self.fit_n_cliffords,
            self.standard_fit_Pideal_y,
            color="orchid",
            lw=3,
            label=rf"$\lambda_r^{{SRB}}$: {self.standard_lambda_r:.4f}",
        )
        axs[1].plot(
            self.fit_n_cliffords,
            self.interleaved_fit_Pideal_y,
            color="aqua",
            lw=3,
            label=rf"$\lambda_r^{{SRB}}$: {self.interleaved_lambda_r:.3f}",
        )
        if True in self.interleave_modes:
            interleaved_probs_00 = self.P00.sel({self.interleave_modes_coord: True})
            interleaved_probs_00.plot(
                ax=axs[0],
                x=self.number_cliffords_coord,
                hue=self.seed_coord,
                alpha=0.2,
                ls=":",
            )
            axs[0].plot(
                self.fit_n_cliffords,
                self.interleaved_fit_y,
                color="magenta",
                lw=3,
                label=f"$p_{{IRB}}$: {self.interleaved_p:.3f}",
            )
            # fidelity based on simple exponential fits
            fidelity = 0.25 + 0.75 * self.interleaved_p / self.standard_p
            title = rf"CZ fidelity = {fidelity:.3f}"
        axs[0].set_ylabel(r"State |00$\rangle$ probability")
        axs[0].axhline(0.25, color="black")
        axs[0].legend()
        axs[1].legend()
        axs[0].set_title(title)
        axs[1].set_title(f"CZ fidelity (Nakamura paper): {self.average_fidelity:0.3f}")

        figures_dictionary[self.coupler] = [fig]


class TwoQubitRBNodeAnalysis(BaseAllCouplersAnalysis):
    single_coupler_analysis_obj = TwoQubitRnBAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
