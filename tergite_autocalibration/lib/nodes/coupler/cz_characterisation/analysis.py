from enum import Enum
from functools import singledispatchmethod

import numpy as np
import xarray as xr
from scipy.optimize import leastsq

from tergite_autocalibration.lib.base.analysis import BaseAnalysis

class CZ_Frequency_And_Amplitude_Analysis(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        self.data_var = list(dataset.data_vars.keys())[0]
        self.S21 = dataset[self.data_var].values
        self.fit_results = {}
        self.qubit = dataset[self.data_var].attrs["qubit"]
        dataset[f"y{self.qubit}"].values = np.abs(self.S21)
        self.dataset = dataset

    def run_fitting(self) -> list[float, float]:
        # There are two types of fitting with different fitting goals.
        # run_fitting_min_coupling_strength is more robust as it will use all measurment data.
        # I recommend using it initially.
        # You can perform a more refined fitting by using run_fitting_max_swap_amp.

        print("WARNING TESTING CZ ANALYSIS")
        return self.run_fitting_find_min()
        # return self.run_fitting_min_coupling_strength()

    def run_fitting_find_min(self):
        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                frequencies_coord = coord
            elif "amplitudes" in coord:
                durations_coord = coord
        freq = self.dataset[frequencies_coord].values  # MHz
        times = self.dataset[durations_coord].values  # ns
        self.amp = times
        self.freq = freq
        freq = freq / 1e6
        times = times
        magnitudes = np.array(
            [[np.linalg.norm(u) for u in v] for v in self.dataset[f"y{self.qubit}"]]
        )
        magnitudes = np.transpose(
            (magnitudes - np.min(magnitudes))
            / (np.max(magnitudes) - np.min(magnitudes))
        )
        min_index = np.argmin(magnitudes)
        min_index = np.unravel_index(min_index, magnitudes.shape)
        self.opt_freq = self.freq[min_index[0]]
        self.opt_cz = self.amp[min_index[1]]
        print(self.opt_freq, self.opt_cz)
        return [self.opt_freq, self.opt_cz]

    def run_fitting_min_coupling_strength(self):
        """
        Find the optimal ac frequency by finding the longest swapping period.
        """
        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                frequencies_coord = coord
            elif "amplitudes" in coord:
                durations_coord = coord
        freq = self.dataset[frequencies_coord].values  # MHz
        times = self.dataset[durations_coord].values  # ns
        self.amp = times
        self.freq = freq
        freq = freq / 1e6
        times = times
        magnitudes = np.array(
            [[np.linalg.norm(u) for u in v] for v in self.dataset[f"y{self.qubit}"]]
        )
        magnitudes = np.transpose(
            (magnitudes - np.min(magnitudes))
            / (np.max(magnitudes) - np.min(magnitudes))
        )
        tstep = times[1] - times[0]
        # ----------- First round fit ------------#
        # Find the corresponding coupling strength and period for each CZ ac frequency
        coupling_strength = []
        freqs = np.fft.fftfreq(magnitudes.shape[1], tstep)
        freqs = freqs[1:]
        for i in range(magnitudes.shape[0]):
            fourier = np.abs(np.fft.fft(magnitudes[i, :], magnitudes.shape[1]))
            fringe = np.abs(freqs[np.argmax(fourier[1:])])
            coupling_strength.append(fringe)
        period = 1 / np.array(coupling_strength)
        coupling_strength = []
        for i, prob in enumerate(magnitudes):
            # p[0]: amp, p[1]: period, p[2]: time_offset, p[4]: decay rate
            def fitfunc(p):
                return (
                    p[0]
                    * np.exp(-p[4] * times)
                    * np.cos(2 * np.pi / p[1] * (times - p[2]))
                    + p[3]
                )

            def errfunc(p):
                return prob - fitfunc(p)

            out = leastsq(
                errfunc,
                np.array(
                    [np.max(prob), period[i], times[np.argmax(prob)], np.max(prob), 0]
                ),
                full_output=1,
            )
            paras = out[0]
            coupling_strength.append(1 / paras[1])
        coupling_strength = np.array(coupling_strength)

        # ----------- Second round fit ------------#
        # The longest gate times is less than 1000 ns, which means that p[1] must be less than 1e3.
        # Thus, coupling_strength must be greater than 1e-3.
        freq = freq[coupling_strength > 1e-3]
        coupling_strength = coupling_strength[coupling_strength > 1e-3]
        if len(coupling_strength) < 4:
            self.opt_freq, self.opt_cz = 0, 0
            print(
                f"No enough available points. Please resweep once again or enlarge sweep range."
            )
        else:
            # ----------- Third round fit ------------#
            cmin = np.mean(coupling_strength)
            fmin_guess = np.mean(freq)
            p0_guess = (coupling_strength[0] - cmin) / (freq[0] - fmin_guess) ** 2
            p1_guess = (coupling_strength[-1] - cmin) / (freq[-1] - fmin_guess) ** 2
            p_guess = np.array([p0_guess, p1_guess, fmin_guess, cmin])

            # Fine-fitting with parabolas in the form of y = a (x - b)^2 + c
            # Because the data may not be symmetric about the axis. We
            # p[0]: parameter a of the left one
            # p[1]: parameter a of the right one
            # p[2]: the symmetric axis, b
            # p[3]: the minimal coupling strength, c
            def fitfunc(p, xs):
                return (
                    np.heaviside(p[2] - xs, 0) * p[0] * (xs - p[2]) ** 2
                    + p[3]
                    + np.heaviside(xs - p[2], 0) * p[1] * (xs - p[2]) ** 2
                )

            def errfunc(p):
                return coupling_strength - fitfunc(p, freq)

            out = leastsq(errfunc, p_guess)
            p = out[0]
            # The symmetric axis must lie in the range of freq.
            # Two as must be both less than zero indiciating a minimum.
            if p[2] > freq[-1] or p[2] < freq[0] or p[0] < 0 or p[1] < 0:
                # The freq range is too small or the swapping period exceeds 1 us, which is also unacceptable.
                print(
                    "You should probably enlarge your sweep range. The optimial point is not in the current range."
                )
                self.opt_freq, self.opt_cz = 0, 0
            else:
                # ----------- Fourth round fit ------------#
                # Fine fit the parameter with 7 points in a small region around the minimum.
                freq_fit = np.linspace(freq[0], freq[-1], 1000)
                data_fit = fitfunc(p, freq_fit)
                f_opt = freq_fit[
                    np.argmin(data_fit)
                ]  # The optimal frequency derived from the fitting
                id_opt = np.argmin(
                    np.abs(freq - f_opt)
                )  # The index of optimal frequency
                id_left = (
                    (id_opt - 3) if (id_opt - 3) > 0 else 0
                )  # The leftmost index of the new region
                id_right = (
                    (id_opt + 4) if (id_opt + 4) < len(freq) else len(freq)
                )  # The rightmost index of the new region
                freq_cut = freq[id_left:id_right]  # The new freq range
                p_guess = [p0_guess, freq[id_opt], coupling_strength[id_opt]]

                def fitfunc(p, xs):  # Now we fit using a parabola
                    return p[0] * (p[1] - xs) ** 2 + p[2]

                def errfunc(p):
                    return coupling_strength[id_left:id_right] - fitfunc(p, freq_cut)

                out = leastsq(errfunc, p_guess)
                p = out[0]
                freq_fit = np.linspace(
                    freq_cut[0], freq_cut[-1], 100
                )  # The final fitting frequency
                data_fit = fitfunc(p, freq_fit)  # The final fitting period
                id_min = np.argmin(
                    coupling_strength[id_left:id_right]
                )  # The experiment data lying the new region
                print("np.min(coupling_strength):", np.min(coupling_strength))
                print("np.min(data_fit):", np.min(data_fit))
                # Compare the experiment data with the fitting data.
                # The minimal experiment data must be valided. It should also lie in the new region.
                if np.min(data_fit) > np.min(coupling_strength) and (
                    id_left <= id_min + id_left <= id_right
                ):
                    f_opt = freq[id_min + id_left]
                    c_opt = np.min(coupling_strength)
                    print("We use the raw measured data.")
                else:  # Otherwise, we use the fitting data.
                    id_opt = np.argmin(data_fit)
                    c_opt = data_fit[id_opt]
                    f_opt = freq_fit[id_opt]
                gate_time = 1 / c_opt
                self.opt_freq, self.opt_cz = f_opt * 1e6, gate_time / 1e9

        return [self.opt_freq, self.opt_cz]

    def run_fitting_max_swap_amp(self):
        """
        Find the optimal ac frequency by finding the largest swapping amplitudes in the first period.
        """
        coords = list(self.dataset.coords)
        freq = self.dataset[coords[1]].values  # MHz
        times = self.dataset[coords[0]].values  # ns
        self.amp = times
        self.freq = freq
        freq = freq / 1e6
        times = times
        magnitudes = np.array(
            [[np.linalg.norm(u) for u in v] for v in self.dataset[f"y{self.qubit}"]]
        )
        magnitudes = np.transpose(
            (magnitudes - np.min(magnitudes))
            / (np.max(magnitudes) - np.min(magnitudes))
        )
        tstep = times[1] - times[0]
        # ----------- First round fit ------------#
        # Find the corresponding coupling strength and period for each CZ ac frequency
        coupling_strength = []
        freqs = np.fft.fftfreq(magnitudes.shape[1], tstep)
        freqs = freqs[1:]
        for i in range(magnitudes.shape[0]):
            fourier = np.abs(np.fft.fft(magnitudes[i, :], magnitudes.shape[1]))
            fringe = np.abs(freqs[np.argmax(fourier[1:])])
            coupling_strength.append(fringe)
        period = 1 / np.array(coupling_strength)
        period_fit = []
        for i, prob in enumerate(magnitudes):
            # p[0]: amp, p[1]: period, p[2]: time_offset, p[4]: decay rate
            def fitfunc(p):
                return (
                    p[0]
                    * np.exp(-p[4] * times)
                    * np.cos(2 * np.pi / p[1] * (times - p[2]))
                    + p[3]
                )

            def errfunc(p):
                return prob - fitfunc(p)

            # print(prob)
            out = leastsq(
                errfunc,
                np.array(
                    [np.max(prob), period[i], times[np.argmax(prob)], np.max(prob), 0]
                ),
                full_output=1,
            )
            p = out[0]
            period_fit.append(p[1])
        period_fit = np.array(period_fit)
        # ----------- Second round fit ------------#
        # We only fit the data in the first fitting period.
        amps = []  # The swapping amplitudes in the first period.
        for i, prob in enumerate(magnitudes):
            times_cut_index = np.argmin(np.abs(times - period_fit[i]))
            times_cut = times[:times_cut_index]

            def fitfunc(p):
                return (
                    p[0]
                    * np.exp(-p[4] * times_cut)
                    * np.cos(2 * np.pi / p[1] * (times_cut - p[2]))
                    + p[3]
                )

            def errfunc(p):
                return prob[:times_cut_index] - fitfunc(p)

            out = leastsq(
                errfunc,
                np.array(
                    [
                        np.max(prob),
                        period_fit[i],
                        times[np.argmax(prob)],
                        np.max(prob),
                        0,
                    ]
                ),
                full_output=1,
            )
            p = out[0]
            amps.append(p[0])
            period_fit[i] = p[1]
        amps = np.array(amps)
        # The longest gate time should be less than 1000 ns, i.e., p[1] must be less than 1e3.
        # Thus, coupling strength must be greater than 1e-3.
        freq = freq[period_fit < 1000]
        amps = amps[period_fit < 1000]
        period_fit = period_fit[period_fit < 1000]
        if len(period_fit) < 4:
            # All swapping periods are too long or there are no swappings at all.
            print(
                f"No enough available points. Please resweep once again or enlarge sweep range."
            )
            self.opt_freq, self.opt_cz = 0, 0
        else:
            # ----------- Third round fit ------------#
            amp_max = np.max(amps)
            fmin_guess = np.mean(freq)
            p0_guess = (amps[0] - amp_max) / (freq[0] - fmin_guess) ** 2
            p1_guess = (amps[-1] - amp_max) / (freq[-1] - fmin_guess) ** 2
            p_guess = np.array([p0_guess, p1_guess, fmin_guess, amp_max])

            def fitfunc(p, xs):
                # Fine-fitting with parabolas in the form of y = a (x - b)^2 + c
                # Because the data may not be symmetric about the axis. We
                # p[0]: parameter a of the left one
                # p[1]: parameter a of the right one
                # p[2]: the symmetric axis, b
                # p[3]: the maximal coupling strength, c
                return (
                    np.heaviside(p[2] - xs, 0) * p[0] * (xs - p[2]) ** 2
                    + p[3]
                    + np.heaviside(xs - p[2], 0) * p[1] * (xs - p[2]) ** 2
                )

            def errfunc(p):
                return amps - fitfunc(p, freq)

            out = leastsq(errfunc, p_guess)
            p = out[0]
            # The symmetric axis must lie in the range of freq.
            # Two as must be both greater than zero indiciating a maximum.
            if p[2] > freq[-1] or p[2] < freq[0] or p[0] > 0 or p[1] > 0:
                print(
                    "You should probably enlarge your sweep range. The optimial point is not in the current range."
                )
                self.opt_freq, self.opt_cz = 0, 0
            else:
                # ----------- Fourth round fit ------------#
                # Fine fit the parameter with 7 points in a small region around the maximum.
                id_opt = np.argmax(fitfunc(p, freq))
                id_left = (id_opt - 3) if (id_opt - 3) > 0 else 0  # The leftmost index
                id_right = (
                    (id_opt + 4) if (id_opt + 4) < len(freq) else len(freq)
                )  # The rightmost index
                freq_cut = freq[id_left:id_right]
                p_guess = [p0_guess, freq[id_opt], amps[id_opt]]

                def fitfunc(p, xs):  # We fit using only one parabola
                    return p[0] * (p[1] - xs) ** 2 + p[2]

                # ----------- find max amplitude ----------#
                def errfunc(p):
                    return amps[id_left:id_right] - fitfunc(p, freq_cut)

                out = leastsq(errfunc, p_guess)
                p = out[0]
                freq_fit = np.linspace(
                    freq_cut[0], freq_cut[-1], 100
                )  # The final fitting frequency
                data_fit = fitfunc(p, freq_fit)  # The final fitting amps
                f_opt = freq_fit[
                    np.argmax(data_fit)
                ]  # Find the optimal fitting frequency.
                id_max = np.argmax(
                    amps
                )  # The index of maximal amplitudes in experiment data.
                # Compare the experiment data with the fitting data.
                # The maximal experiment data must be valided. It should also lie in the new region.
                if np.max(data_fit) < np.max(amps) and (id_left <= id_max <= id_right):
                    f_opt = freq[id_max]
                    gate_time = period_fit[id_max]
                    print("We use the raw measured data.")
                else:
                    # ---------- fit gate time ----------------#
                    def errfunc(p):
                        return period_fit[id_left:id_right] - fitfunc(p, freq_fit)

                    p0_guess = (period_fit[id_left] - period_fit[id_opt]) / (
                        freq[id_left] - freq[id_opt]
                    ) ** 2
                    p_guess = [p0_guess, freq[id_opt], period_fit[id_opt]]
                    out = leastsq(errfunc, p_guess)
                    gate_time = fitfunc(out[0], f_opt)
                # ---------- show final result ------------#
                print(f_opt, gate_time)
                self.opt_freq = f_opt * 1e6
                self.opt_cz = gate_time / 1e9
        return [self.opt_freq, self.opt_cz]

    def plotter(self, axis):
        datarray = self.dataset[f"y{self.qubit}"]
        qubit = self.qubit
        datarray.plot(ax=axis, cmap="RdBu_r")
        # fig = axis.pcolormesh(amp,freq,magnitudes,shading='nearest',cmap='RdBu_r')
        axis.scatter(
            self.opt_freq,
            self.opt_cz,
            c="r",
            label="CZ Amplitude = {:.3f} V".format(self.opt_cz),
            marker="X",
            s=200,
            edgecolors="k",
            linewidth=1.5,
            zorder=10,
        )
        # plt.scatter(opt_swap,opt_freq,c='b',label = 'SWAP12 Duration= {:.2f} V'.format(opt_swap),marker='X',s=200,edgecolors='k', linewidth=1.5,zorder=10)
        axis.vlines(
            self.opt_freq,
            self.amp[0],
            self.amp[-1],
            label="Frequency Detuning = {:.2f} MHz".format(self.opt_freq / 1e6),
            colors="k",
            linestyles="--",
            linewidth=1.5,
        )
        axis.hlines(
            self.opt_cz,
            self.freq[0],
            self.freq[-1],
            colors="k",
            linestyles="--",
            linewidth=1.5,
        )
        # axis.legend(loc = 'lower center', bbox_to_anchor=(-0.15, -0.36, 1.4, .102), mode='expand', ncol=2,
        #             title = 'Optimal Gate Parameters', columnspacing=200,borderpad=1)
        # cbar = plt.colorbar(fig)
        # cbar.set_label('|2>-state Population', labelpad=10)
        axis.set_xlim([self.freq[0], self.freq[-1]])
        axis.set_ylim([self.amp[0], self.amp[-1]])
        axis.set_ylabel("Parametric Drive amplitude (V)")
        axis.set_xlabel("Frequency Detuning (Hz)")
        axis.set_title(f"CZ Chevron - Qubit {self.qubit[1:]}")
