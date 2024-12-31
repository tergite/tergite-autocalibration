# This code is part of Tergite
#
# (C) Copyright Liangyu Chen 2024
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

from enum import Enum
from functools import singledispatchmethod

import matplotlib.patches as mpatches
import numpy as np
from scipy.optimize import leastsq

from ....base.analysis import (
    BaseAllCouplersAnalysis,
    BaseCouplerAnalysis,
    BaseQubitAnalysis,
)


class SweepResultStatus(Enum):
    NOT_AVAILABLE = 0
    NOT_FOUND = 1
    FOUND = 2


class OptimalResult:
    def __init__(self, sweep_para, unit):
        """
        Parameters
        ----------
        id
            Id of the data, e.g., tuid
        sweep_para
            The para to be swept
        unit
            The unit of sweep_para
        """
        # self.id = id
        self.sweep_para = sweep_para
        self.sweep_para_unit = unit
        self._result = None
        self.status = SweepResultStatus.NOT_AVAILABLE

    def get_result(self):
        """
        If we found the optimal result, check if we need some
        supplementary information asscoiated with the optimal result.
        If so, we return them as a tuple.
        """
        if self.status != SweepResultStatus.FOUND:
            return self.status
        else:
            result = (self.sweep_para, self._result, self.sweep_para_unit)
            result_add = getattr(self, "result_add", None)
            if result_add is None:
                return result
            else:
                return result, result_add

    @singledispatchmethod
    def set_result(self, result: float):
        self.status = SweepResultStatus.FOUND
        self._result = result

    @set_result.register
    def _(self, result: tuple):
        self.status = SweepResultStatus.FOUND
        self._result, self.result_add = result

    def set_not_found(self):
        self.status = SweepResultStatus.NOT_FOUND


class ResetChevronQubitAnalysis(BaseQubitAnalysis):
    def analyse_qubit(self):

        self.fit_results = {}
        self.result = OptimalResult(f"reset_pulse_durations", "s")

        for coord in self.dataset[self.data_var].coords:
            if "amplitudes" in coord:
                self.amplitudes_coord = coord
            elif "durations" in coord:
                self.durations_coord = coord
        amps = self.dataset[self.amplitudes_coord].values
        times = self.dataset[self.durations_coord].values  # ns
        self.times = times
        self.amps = amps
        magnitudes = np.array(
            [[np.linalg.norm(u) for u in v] for v in self.magnitudes[f"{self.qubit}"]]
        )
        self.min = np.min(magnitudes)
        magnitudes = np.transpose(
            (magnitudes - np.min(magnitudes))
            / (np.max(magnitudes) - np.min(magnitudes))
        )
        direct = True
        if direct:
            min_index = np.argmin(magnitudes)
            min_index = np.unravel_index(min_index, magnitudes.shape)
            self.opt_freq = self.amps[min_index[0]]
            self.opt_cz = self.times[min_index[1]]
            # print(self.opt_freq, self.opt_cz)
        else:
            tstep = times[1] - times[0]
            # ----------- First round fit ------------#
            cs = []
            freqs = np.fft.fftfreq(magnitudes.shape[1], tstep)
            freqs = freqs[1:]
            try:
                for i in range(magnitudes.shape[0]):
                    fourier = np.abs(np.fft.fft(magnitudes[i, :], magnitudes.shape[1]))
                    fringe = np.abs(freqs[np.argmax(fourier[1:])])
                    cs.append(fringe)
                period = 1 / np.array(cs)
                period_fit = []
                for i, prob in enumerate(magnitudes):

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
                            [
                                np.max(prob),
                                period[i],
                                times[np.argmax(prob)],
                                np.max(prob),
                                0,
                            ]
                        ),
                        full_output=1,
                    )
                    p = out[0]
                    period_fit.append(p[1])
                period_fit = np.array(period_fit)
                # ----------- Second round fit ------------#
                amps = []
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
                # The longest gate times is less than 500ns, which means that p[1] must be less than 0.5*1e3.
                # Thus, cs must be greater than 2*1e-3.
                freq = freq[period_fit < 500]
                amps = amps[period_fit < 500]
                period_fit = period_fit[period_fit < 500]
                if len(period_fit) < 4:
                    # axes[2].set_title("No enough available points.")
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
                        return (
                            np.heaviside(p[2] - xs, 0) * p[0] * (xs - p[2]) ** 2
                            + p[3]
                            + np.heaviside(xs - p[2], 0) * p[1] * (xs - p[2]) ** 2
                        )

                    def errfunc(p):
                        return amps - fitfunc(p, freq)

                    out = leastsq(errfunc, p_guess)
                    p = out[0]

                    if p[2] > freq[-1] or p[2] < freq[0] or p[0] > 0 or p[1] > 0:
                        print(
                            "You should probably enlarge your sweep range. The optimial point is not in the current range."
                        )
                        self.opt_freq, self.opt_cz = 0, 0
                    else:
                        # ----------- Fourth round fit ------------#
                        id_opt = np.argmax(fitfunc(p, freq))
                        id_left = (id_opt - 3) if (id_opt - 3) > 0 else 0
                        id_right = (
                            (id_opt + 4) if (id_opt + 4) < len(freq) else len(freq)
                        )
                        xs = freq[id_left:id_right]
                        p_guess = [p0_guess, freq[id_opt], amps[id_opt]]

                        def fitfunc(p, xs):
                            return p[0] * (p[1] - xs) ** 2 + p[2]

                        # ----------- find max amplitude ----------#
                        def errfunc(p):
                            return amps[id_left:id_right] - fitfunc(p, xs)

                        out = leastsq(errfunc, p_guess)
                        p = out[0]
                        freq_fit = np.linspace(xs[0], xs[-1], 100)
                        data_fit = fitfunc(p, freq_fit)
                        f_opt = freq_fit[np.argmax(data_fit)]

                        # ---------- find gate time ---------------#
                        def errfunc(p):
                            return period_fit[id_left:id_right] - fitfunc(p, xs)

                        p0_guess = (period_fit[id_left] - period_fit[id_opt]) / (
                            freq[id_left] - freq[id_opt]
                        ) ** 2
                        p_guess = [p0_guess, freq[id_opt], period_fit[id_opt]]
                        out = leastsq(errfunc, p_guess)
                        gate_time = fitfunc(out[0], f_opt)
                        # ---------- show final result ------------#

                        # print(f_opt, gate_time)
                        self.opt_freq = f_opt * 1e6
                        self.opt_cz = gate_time / 1e9
            except:
                print("Something wrong with the fitting process.")
                self.opt_freq, self.opt_cz = 0, 0
        return [self.opt_freq, self.opt_cz]

    def plotter(self, axis):
        datarray = self.magnitudes[f"{self.qubit}"]
        datarray.plot(ax=axis, x=self.amplitudes_coord, cmap="RdBu_r")
        axis.scatter(0, 0, label="Min = {:.4f}".format(self.min))
        axis.scatter(
            self.opt_freq,
            self.opt_cz,
            c="r",
            label="Duration = {:.1f} ns".format(self.opt_cz * 1e9),
            marker="*",
            s=200,
            edgecolors="k",
            linewidth=0.5,
            zorder=10,
        )
        axis.vlines(
            self.opt_freq,
            self.times[0],
            self.times[-1],
            label="Amplitude = {:.5f} V".format(self.opt_freq),
            colors="k",
            linestyles="--",
            linewidth=1.5,
        )
        axis.hlines(
            self.opt_cz,
            self.amps[0],
            self.amps[-1],
            colors="k",
            linestyles="--",
            linewidth=1.5,
        )
        axis.set_xlim([self.amps[0], self.amps[-1]])
        axis.set_ylim([self.times[0], self.times[-1]])
        axis.set_ylabel("Drive Durations (s)")
        axis.set_xlabel("Drive Amplitude (V)")
        axis.set_title(f"Reset Chevron - Qubit {self.qubit[1:]}")
        axis.legend()  # Add legend to the plot

        # Customize plot as needed
        handles, labels = axis.get_legend_handles_labels()
        patch = mpatches.Patch(color="red", label=f"{self.qubit}")
        handles.append(patch)
        axis.legend(handles=handles, fontsize="small")


class ResetChevronCouplerAnalysis(BaseCouplerAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.data_path = ""
        self.q1 = ""
        self.q2 = ""
        pass

    def analyze_coupler(self) -> list[float, float, float]:
        self.fit_results = {}

        q1_data_var = [
            data_var
            for data_var in self.dataset.data_vars
            if self.name_qubit_1 in data_var
        ]
        ds1 = self.dataset[q1_data_var]
        matching_coords = [coord for coord in ds1.coords if self.name_qubit_1 in coord]
        if matching_coords:
            selected_coord_name = matching_coords[0]
            ds1 = ds1.sel({selected_coord_name: slice(None)})

        self.q1 = ResetChevronQubitAnalysis(self.name, self.redis_fields)
        res1 = self.q1.process_qubit(ds1, q1_data_var[0])

        q2_data_var = [
            data_var
            for data_var in self.dataset.data_vars
            if self.name_qubit_2 in data_var
        ]
        ds2 = self.dataset[q2_data_var]
        matching_coords = [coord for coord in ds2.coords if self.name_qubit_2 in coord]
        if matching_coords:
            selected_coord_name = matching_coords[0]
            ds2 = ds2.sel({selected_coord_name: slice(None)})

        self.q2 = ResetChevronQubitAnalysis(self.name, self.redis_fields)
        res2 = self.q2.process_qubit(ds2, q2_data_var[0])

        return res1

    def plotter(self, primary_axis, secondary_axis):
        self.q1.plotter(primary_axis)
        self.q2.plotter(secondary_axis)


class ResetChevronNodeAnalysis(BaseAllCouplersAnalysis):
    single_coupler_analysis_obj = ResetChevronCouplerAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def save_plots(self):
        super().save_plots()
