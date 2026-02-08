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
                self.number_cliffords = self.S21[coord]
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

        self.P00 = self.state_probabilities(0, 0)
        self.P01 = self.state_probabilities(0, 1)
        self.P10 = self.state_probabilities(1, 0)
        self.P11 = self.state_probabilities(1, 1)
        self.P02 = self.state_probabilities(0, 2)
        self.P12 = self.state_probabilities(1, 2)
        self.P20 = self.state_probabilities(2, 0)
        self.P21 = self.state_probabilities(2, 1)
        self.P22 = self.state_probabilities(2, 2)
        self.P_leakage = self.P02 + self.P12 + self.P20 + self.P21 + self.P22

        self.mean_probabilities_00 = self.P00.mean(self.seed_coord)
        self.mean_probabilities_01 = self.P01.mean(self.seed_coord)
        self.mean_probabilities_10 = self.P10.mean(self.seed_coord)
        self.mean_probabilities_11 = self.P11.mean(self.seed_coord)
        self.mean_probabilities_02 = self.P02.mean(self.seed_coord)
        self.mean_probabilities_20 = self.P20.mean(self.seed_coord)
        self.mean_probabilities_21 = self.P21.mean(self.seed_coord)
        self.mean_probabilities_12 = self.P12.mean(self.seed_coord)
        self.mean_probabilities_22 = self.P22.mean(self.seed_coord)

        # probabilities to of states in the computational subspace
        self.mean_probabilities_chi_1 = (
            self.mean_probabilities_00
            + self.mean_probabilities_01
            + self.mean_probabilities_10
            + self.mean_probabilities_11
        )

        self.standard_mean_probs_00 = self.mean_probabilities_00.sel(
            {self.interleave_modes_coord: False}
        )

        self.standard_mean_probs_chi_1 = self.mean_probabilities_chi_1.sel(
            {self.interleave_modes_coord: False}
        )

        self.standard_reduced_ideal_probabilities = (
            self.standard_mean_probs_00
            - self.standard_mean_probs_chi_1 / computational_space_dimension
        )
        self.interleaved_mean_probs_00 = self.mean_probabilities_00.sel(
            {self.interleave_modes_coord: True}
        )

        self.interleaved_mean_probs_chi_1 = self.mean_probabilities_chi_1.sel(
            {self.interleave_modes_coord: True}
        )
        self.interleaved_reduced_ideal_probabilities = (
            self.interleaved_mean_probs_00
            - self.interleaved_mean_probs_chi_1 / computational_space_dimension
        )

        # Fit 1: fit probabilities of the computational states eq. K14
        standard_guess_Pchi_1 = self.single_model.guess(
            data=self.standard_mean_probs_chi_1.values, m=self.number_cliffords.values
        )

        standard_fit_Pchi_1_result = self.single_model.fit(
            self.standard_mean_probs_chi_1.values,
            params=standard_guess_Pchi_1,
            m=self.number_cliffords.values,
        )
        #################

        # Fit 2: fit the reduced ideal probabilities eq. K15
        standard_guess_Pideal = self.single_model.guess(
            data=self.standard_reduced_ideal_probabilities.values,
            m=self.number_cliffords.values,
        )

        standard_fit_Pideal_result = self.single_model.fit(
            self.standard_reduced_ideal_probabilities.values,
            params=standard_guess_Pideal,
            m=self.number_cliffords.values,
        )
        #################

        standard_guess = self.single_model.guess(
            data=self.standard_mean_probs_00.values, m=self.number_cliffords.values
        )
        standard_fit_result = self.single_model.fit(
            self.standard_mean_probs_00.values,
            params=standard_guess,
            m=self.number_cliffords.values,
        )

        self.fit_n_cliffords = np.linspace(
            self.number_cliffords.values[0], self.number_cliffords.values[-1], 200
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
            self.interleaved_mean_probs_00 = self.mean_probabilities_00.sel(
                {self.interleave_modes_coord: True}
            )
            self.interleaved_mean_probs_chi_1 = self.mean_probabilities_chi_1.sel(
                {self.interleave_modes_coord: True}
            )
            interleaved_guess = self.single_model.guess(
                data=self.interleaved_mean_probs_00.values,
                m=self.number_cliffords.values,
            )
            interleaved_fit_result = self.single_model.fit(
                self.interleaved_mean_probs_00.values,
                params=interleaved_guess,
                m=self.number_cliffords.values,
            )
            interleaved_guess_Pchi_1 = self.single_model.guess(
                data=self.interleaved_mean_probs_chi_1.values,
                m=self.number_cliffords.values,
            )

            interleaved_fit_Pchi_1_result = self.single_model.fit(
                self.interleaved_mean_probs_chi_1.values,
                params=interleaved_guess_Pchi_1,
                m=self.number_cliffords.values,
            )
            interleaved_guess_Pideal = self.single_model.guess(
                data=self.interleaved_reduced_ideal_probabilities.values,
                m=self.number_cliffords.values,
            )

            interleaved_fit_Pideal_result = self.single_model.fit(
                self.interleaved_reduced_ideal_probabilities.values,
                params=interleaved_guess_Pideal,
                m=self.number_cliffords.values,
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
            # print(f"{ interleaved_fit_Pideal_result.params = }")
            self.interleaved_lambda_r = interleaved_fit_Pideal_result.params["p"].value
            self.interleaved_p = interleaved_fit_result.params["p"].value

        self.standard_p = standard_fit_result.params["p"].value
        self.standard_lambda_L = standard_fit_Pchi_1_result.params["p"].value
        self.standard_AM = standard_fit_Pchi_1_result.params["A"].value
        self.standard_BM = standard_fit_Pchi_1_result.params["B"].value
        print(f"{ standard_fit_Pideal_result.params = }")
        self.standard_lambda_r = standard_fit_Pideal_result.params["p"].value

        L1_standard = (1 - self.standard_lambda_L) * (1 - self.standard_AM)
        L2_standard = (1 - self.standard_lambda_L) * self.standard_AM
        L1_interleaved = (1 - self.interleaved_lambda_L) * (1 - self.interleaved_AM)
        L2_interleaved = (1 - self.interleaved_lambda_L) * self.interleaved_AM
        self.one_minus_L1_CZ = (1 - L1_interleaved) / (1 - L1_standard)
        self.lambda_r_CZ = self.interleaved_lambda_r / self.standard_lambda_r

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

        title = r"State |00$\rangle$"
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
            ax=axs[0],
            x=self.number_cliffords_coord,
            hue=self.seed_coord,
            alpha=0.2,  # marker="o", ls=""
        )
        standard_probs_chi_1.plot(
            ax=axs[1],
            x=self.number_cliffords_coord,
            hue=self.seed_coord,
            alpha=0.2,  # marker="o", ls=""
        )
        standard_probs_reduced_ideal.plot(
            ax=axs[1],
            x=self.number_cliffords_coord,
            hue=self.seed_coord,
            alpha=0.2,  # marker="o", ls=""
        )
        interleaved_probs_chi_1.plot(
            ax=axs[1],
            x=self.number_cliffords_coord,
            hue=self.seed_coord,
            alpha=0.2,  # marker="o", ls=""
        )
        interleaved_probs_reduced_ideal.plot(
            ax=axs[1],
            x=self.number_cliffords_coord,
            hue=self.seed_coord,
            alpha=0.2,  # marker="o", ls=""
        )
        axs[0].plot(
            self.fit_n_cliffords,
            self.standard_fit_y,
            color="red",
            lw=3,
            label=f"p: {self.standard_p:.3f}",
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
            # self.standard_fit_P0_y,
            self.standard_fit_Pideal_y,
            color="orchid",
            lw=3,
            # label=rf"$\lambda_2$: {self.standard_lambda_2:.4f}",
            label=rf"$\lambda_r^{{SRB}}$: {self.standard_lambda_r:.4f}",
        )
        axs[1].plot(
            self.fit_n_cliffords,
            # self.interleaved_fit_P0_y,
            self.interleaved_fit_Pideal_y,
            color="aqua",
            lw=3,
            # label=rf"$\lambda_2$: {self.interleaved_lambda_2:.4f}",
            label=rf"$\lambda_r^{{SRB}}$: {self.interleaved_lambda_r:.4f}",
        )
        if True in self.interleave_modes:
            interleaved_probs_00 = self.P00.sel({self.interleave_modes_coord: True})
            interleaved_probs_00.plot(
                ax=axs[0],
                x=self.number_cliffords_coord,
                hue=self.seed_coord,
                alpha=0.2,  # marker="o", ls=""
                ls=":",
            )
            axs[0].plot(
                self.fit_n_cliffords,
                self.interleaved_fit_y,
                color="magenta",
                lw=3,
                label=f"p: {self.interleaved_p:.3f}",
            )
            fidelity = 0.25 + 0.75 * self.interleaved_p / self.standard_p
            title = r"State |00$\rangle$" + "  " + f"F = {fidelity:.4f}"
        axs[0].axhline(0.25, color="black")
        # axs[1].axhline(0.75, color="black")
        axs[0].legend()
        axs[1].legend()
        axs[0].set_title(title)
        axs[1].set_title(f"CZ fidelity: {self.average_fidelity:0.3f}")

        # self.P01.plot(
        #     ax=axs[0][1],
        #     x=self.number_cliffords_coord,
        #     hue=self.seed_coord,
        #     alpha=0.2,  # marker="o", ls=""
        # )
        # axs[0][1].set_title(r"State |01$\rangle$")
        # self.P02.plot(
        #     ax=axs[0][2],
        #     x=self.number_cliffords_coord,
        #     hue=self.seed_coord,
        #     alpha=0.2,  # marker="o", ls=""
        # )
        # axs[0][2].set_title(r"State |02$\rangle$")
        # self.P11.plot(
        #     ax=axs[1][1],
        #     x=self.number_cliffords_coord,
        #     hue=self.seed_coord,
        #     alpha=0.2,  # marker="o", ls=""
        # )
        # axs[0][2].plot(
        #     self.fit_n_cliffords,
        #     self.inverted_fit_y_02,
        #     color="green",
        #     lw=3,
        #     label=self.leakage_02,
        # )
        # axs[0][2].legend()
        # axs[1][1].set_title(r"State |11$\rangle$")
        # axs[0][1].set_title(r"Control Leakage |2X$\rangle$")
        # axs[0][1].plot(
        #     self.fit_n_cliffords,
        #     self.inverted_fit_y_control,
        #     color="green",
        #     lw=3,
        #     label=self.control_leakage,
        # )
        # axs[0][1].legend()
        # self.P_leakage.plot(
        #     ax=axs[0][1],
        #     x=self.number_cliffords_coord,
        #     hue=self.seed_coord,
        #     alpha=0.2,  # marker="o", ls=""
        # )
        # axs[1][0].set_title(r"Target Leakage |X2$\rangle$")
        # axs[1][0].plot(
        #     self.fit_n_cliffords,
        #     self.inverted_fit_y_target,
        #     color="green",
        #     lw=3,
        #     label=self.target_leakage,
        # )
        # axs[1][0].legend()
        # axs[1][1].set_title("Leakage States")
        # axs[1][1].plot(
        #     self.fit_n_cliffords,
        #     self.inverted_fit_y_leakage,
        #     color="green",
        #     lw=3,
        #     label=self.leakage,
        # )
        # axs[1][1].legend()
        figures_dictionary[self.coupler] = [fig]


class TwoQubitRBNodeAnalysis(BaseAllCouplersAnalysis):
    single_coupler_analysis_obj = TwoQubitRnBAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
