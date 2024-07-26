import itertools

import lmfit
import numpy as np
import xarray as xr
from matplotlib import pyplot as plt
from numpy.linalg import inv
from quantify_core.analysis.fitting_models import fft_freq_phase_guess
from scipy.linalg import norm
from scipy.optimize import minimize
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import confusion_matrix

from tergite_autocalibration.config.coupler_config import qubit_types
from ....base.analysis import BaseAnalysis


def mitigate(v, cm_inv):
    u = np.dot(v, cm_inv)

    # print(u,np.sum(u))
    def m(t):
        return norm(u - np.array(t))

    def con(t):
        return t[0] + t[1] + t[2] - 1

    cons = (
        {"type": "eq", "fun": con},
        {"type": "ineq", "fun": lambda t: t[0]},
        {"type": "ineq", "fun": lambda t: t[1]},
        {"type": "ineq", "fun": lambda t: t[2]},
    )
    result = minimize(m, v, method="SLSQP", constraints=cons)
    w = np.abs(np.round(result.x, 10))
    # print(w)
    return w



class ProcessTomographyAnalysis(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        self.data_var = list(dataset.data_vars.keys())[0]
        self.qubit = dataset[self.data_var].attrs["qubit"]
        for coord in dataset.coords:
            if f"control_ons" in str(coord):
                self.sweep_coord = coord
            elif f"ramsey_phases" in str(coord):
                self.state_coord = coord
            elif "shot" in str(coord):
                self.shot_coord = coord
        # self.S21 = dataset[data_var].values
        self.independents = np.array(
            [float(val) for val in dataset[self.state_coord].values[:-3]]
        )
        self.calibs = dataset[self.state_coord].values[-3:]
        self.sweeps = dataset.coords[self.sweep_coord]
        self.shots = len(dataset[self.shot_coord].values)
        self.fit_results = {}
        # dataset[f'y{self.qubit}'].values = np.abs(self.S21)
        self.dataset = dataset

    def run_fitting(self):
        # self.testing_group = 0
        self.dynamic = self.dataset.attrs["node"] == "cz_dynamic_phase"
        self.all_magnitudes = []
        for indx, _ in enumerate(self.sweeps):
            # Calculate confusion matrix from calibration shots
            y = np.repeat(self.calibs, self.shots)
            IQ_complex = np.array([])
            for state, _ in enumerate(self.calibs):
                IQ_complex_0 = self.dataset[self.data_var].isel(
                    {self.sweep_coord: indx, self.state_coord: -3 + state}
                )
                IQ_complex = np.append(IQ_complex, IQ_complex_0)
            I = IQ_complex.real.flatten()
            Q = IQ_complex.imag.flatten()
            IQ = np.array([I, Q]).T
            # IQ = IQ_complex.reshape(-1,2)
            # breakpoint()
            lda = LinearDiscriminantAnalysis(solver="svd", store_covariance=True)
            cla = lda.fit(IQ, y)
            y_pred = cla.predict(IQ)

            cm = confusion_matrix(y, y_pred)
            cm_norm = confusion_matrix(y, y_pred, normalize="true")
            # print(f"{cm = }")
            cm_inv = inv(cm_norm)
            assignment = np.trace(cm_norm) / len(self.calibs)
            # print(f'{assignment = }')
            # print(f'{cm_norm = }')
            # disp = ConfusionMatrixDisplay(confusion_matrix=cm_norm)
            # disp.plot()
            # plt.show()

            # Classify data shots
            raw_data = self.dataset[self.data_var].isel({self.sweep_coord: indx}).values
            raw_shape = raw_data.shape
            I = raw_data.real.flatten()
            Q = raw_data.imag.flatten()
            IQ = np.array([I, Q]).T
            data_y_pred = cla.predict(IQ.reshape(-1, 2))
            # breakpoint()
            data_y_pred = np.transpose(data_y_pred.reshape(raw_shape))
            data_res_shape = list(data_y_pred.shape[:-1])
            data_res_shape.append(len(self.calibs))

            data_res = np.array([])
            for sweep in data_y_pred:
                uniques, counts = np.unique(sweep, return_counts=True)
                raw_prob = [0]*len(self.calibs)
                for state_id,state in enumerate(uniques):
                    raw_prob[int(state)] = counts[state_id]/len(sweep)
                # print(f"{raw_prob = }")
                mitigate_prob = mitigate(raw_prob, cm_inv)
                data_res = np.append(data_res, mitigate_prob)
            data_res = data_res.reshape(data_res_shape)
            self.all_magnitudes.append(data_res)
        self.all_magnitudes = np.array(self.all_magnitudes)
        # Fitting the 1 state data
        self.g_magnitudes = self.all_magnitudes[:, :-3, 0]
        self.e_magnitudes = self.all_magnitudes[:, :-3, 1]
        self.f_magnitudes = self.all_magnitudes[:, :-3, 2]

        # self.freq = self.dataset[f'control_ons{self.qubit}'].values
        # self.amp = self.dataset[f'ramsey_phases{self.qubit}'].values
        # magnitudes = self.dataset[f'y{self.qubit}'].values
        # self.magnitudes = np.transpose(magnitudes)
        # self.magnitudes = np.transpose((magnitudes - np.min(magnitudes))/(np.max(magnitudes)-np.min(magnitudes)))
        # breakpoint()
        # self.fit_independents = self.independents
        # self.fit_ys = []

        # for n, magnitude in enumerate(self.magnitudes):
        #     if qubit_types[self.qubit] == "Target":
        #         if n == 0:
        #             self.fit_ys.append(
        #                 [0, 0, 0, 1, 1, 1, 0, 0, 0]
        #             )  # Control - ResetOff
        #         else:
        #             self.fit_ys.append([0, 0, 0, 0, 0, 0, 0, 0, 0])  # Target - ResetOn
        #     else:
        #         if n == 0:
        #             self.fit_ys.append([0, 1, 0, 0, 1, 0, 0, 1, 0])  # Target - ResetOff
        #         else:
        #             self.fit_ys.append(
        #                 [0, 1, 0, 0, 1, 0, 0, 1, 0]
        #             )  # Target - ResetOn no leakage reduction
        #             # self.fit_ys.append([0,1,1,0,1,1,0,1,1]) # Control - ResetOn

        #     # if qubit_types[self.qubit] == 'Target':
        #     #     if n == 0:
        #     #         self.fit_ys.append([0,1,0,0,1,0,0,1,0]) # Target - ResetOff
        #     #     else:
        #     #         self.fit_ys.append([0,0,0,0,0,0,0,0,0]) # Target - ResetOn
        #     # else:
        #     #     if n == 0:
        #     #         self.fit_ys.append([0,0,0,1,1,1,0,0,0]) # Control - ResetOff
        #     #     else:
        #     #         self.fit_ys.append([0,0,0,1,1,1,1,1,1]) # Control - ResetOn
        # self.fit_ys = np.array(self.fit_ys)
        # self.pop_loss = 1 - np.sum(np.abs(self.magnitudes - self.fit_ys)) / 9
        # self.leakage = np.mean(self.f_magnitudes[-1])

        g_magnitudes_str = ",".join(
            str(element) for element in list(self.g_magnitudes.flatten())
        )

        e_magnitudes_str = ",".join(
            str(element) for element in list(self.e_magnitudes.flatten())
        )
        f_magnitudes_str = ",".join(
            str(element) for element in list(self.f_magnitudes.flatten())
        )

        print(f"{self.g_magnitudes = }")
        print(f"{self.e_magnitudes = }")
        print(f"{self.f_magnitudes = }")
        return [g_magnitudes_str,e_magnitudes_str, f_magnitudes_str]

    def plotter(self, axis):
        # datarray = self.dataset[f'y{self.qubit}']
        # qubit = self.qubit
        state = ["0", "1", "2"]
        states = list(itertools.product(state, state))
        states = [state[0] + state[1] for state in states]

        label = ["Reset Off", "Reset On"]
        name = "Reset"
        x = range(len(label))
        marker = [".", "*", "v", "s"]
        colors = plt.get_cmap("RdBu_r")(np.linspace(0.2, 0.8, len(x)))
        # colors = plt.get_cmap('tab20c')

        for index, magnitude in enumerate(self.all_magnitudes):
            axis.plot(
                self.independents,
                magnitude[:-3, 0],
                f"{marker[0]}",
                # c=colors[index],
                # label=f"|1> {label[index]}",
            )

            axis.plot(
                self.independents,
                magnitude[:-3, 1],
                f"{marker[1]}",
                # c=colors[index],
                # label=f"|1> {label[index]}",
            )
            # axis.plot(self.independents,magnitude[:-3,1],f'{marker[index]}',c = colors(2+4),label=f'|1> {label[index]}')
            axis.plot(
                self.independents,
                magnitude[:-3, 2],
                f"{marker[2]}",
                # c=colors[index],
                # label=f"|2> {label[index]}",
            )

        # for index, magnitude in enumerate(self.magnitudes):
            # breakpoint()
            # axis.plot(self.fit_independents, self.fit_ys[index], "-", c=colors[index])
            # axis.vlines(self.opt_cz[index],-10,10,colors='gray',linestyles='--',linewidth=1.5)

        # axis.plot(
        #     [],
        #     [],
        #     alpha=0,
        #     label="Reset Fidelity = {:.3f}".format(self.pop_loss),
        #     zorder=-10,
        # )
        # axis.plot(
        #     [], [], alpha=0, label="Leakage = {:.3f}".format(self.leakage), zorder=-10
        # )
        axis.set_xlim([self.independents[0], self.independents[-1]])
        axis.legend(loc="upper right")
        axis.set_ylim(-0.01, 1.01)
        axis.set_xlabel("State")
        axis.set_ylabel("Population")
        axis.set_xticklabels(states)
        axis.set_title(
            f"{name} Calibration - {qubit_types[self.qubit]} Qubit {self.qubit[1:]}"
        )
