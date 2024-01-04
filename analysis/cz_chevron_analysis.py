from functools import singledispatchmethod
import numpy as np
import xarray as xr
from enum import Enum
import matplotlib.pyplot as plt
from scipy.optimize import leastsq
# from utilities.redis_helper import fetch_redis_params
# from quantify_core.analysis.fitting_models import fft_freq_phase_guess
# from utilities.QPU_connections_visualization import edge_group

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
    def set_result(self, result:float):
        self.status = SweepResultStatus.FOUND
        self._result = result

    @set_result.register
    def _(self, result:tuple):
        self.status = SweepResultStatus.FOUND
        self._result, self.result_add = result

    def set_not_found(self):
        self.status = SweepResultStatus.NOT_FOUND

class CZChevronAnalysis():
    def  __init__(self,dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        self.S21 = dataset[data_var].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']
        dataset[f'y{self.qubit}'].values = np.abs(self.S21)
        self.dataset = dataset
        self.result = OptimalResult( f'cz_pulse_frequencies_sweep', "MHz")

    def run_fitting(self):
        import pdb
        pdb.set_trace()
        freq = self.dataset[f'cz_pulse_frequencies_sweep{self.qubit}'].values # MHz
        times = self.dataset[f'cz_pulse_durations{self.qubit}'].values # ns
        self.amp = times
        self.freq = freq
        freq = freq/1e6
        times = times*1e9
        magnitudes = np.array([[np.linalg.norm(u) for u in v] for v in self.dataset[f'y{self.qubit}']])
        magnitudes = np.transpose((magnitudes - np.min(magnitudes))/(np.max(magnitudes)-np.min(magnitudes)))
        fig, axes = plt.subplots(1, 3, figsize=(20,5))
        sc = axes[0].imshow(magnitudes, aspect='auto', cmap='jet', extent=[times[0], times[-1], freq[-1], freq[0]])
        plt.colorbar(sc)
        axes[0].set_xlabel("Times")
        axes[0].set_ylabel("Frequency")
        axes[0].set_xlim(times[0], times[-1])
        axes[0].set_ylim(freq[-1], freq[0])
        tstep = times[1] - times[0]
        #----------- First round fit ------------#
        cs = []
        freqs = np.fft.fftfreq(magnitudes.shape[1], tstep)
        freqs = freqs[1:]
        try:
            for i in range(magnitudes.shape[0]):
                fourier = np.abs(np.fft.fft(magnitudes[i,:], magnitudes.shape[1]))
                fringe = np.abs(freqs[np.argmax(fourier[1:])])
                cs.append(fringe)
            period = 1 / np.array(cs)
            period_fit = []
            for i, prob in enumerate(magnitudes):
                def fitfunc(p):
                    return p[0] * np.exp(-p[4] * times) * np.cos(2 * np.pi / p[1] * (times - p[2])) + p[3]
                def errfunc(p):
                    return prob - fitfunc(p)
                # print(prob)
                out = leastsq(errfunc, np.array([np.max(prob), period[i], times[np.argmax(prob)], np.max(prob), 0]), full_output=1)
                p = out[0]
                axes[1].plot(times, prob, 'o', markersize=5)
                axes[1].plot(times, fitfunc(p), '-.', linewidth=1)
                period_fit.append(p[1])
            period_fit = np.array(period_fit)
            #----------- Second round fit ------------#
            # Only fit the data in the first period
            amps = []
            for i, prob in enumerate(magnitudes):
                times_cut_index = np.argmin(np.abs(times - period_fit[i]))
                times_cut = times[:times_cut_index]
                def fitfunc(p):
                    return p[0] * np.exp(-p[4] * times_cut) * np.cos(2 * np.pi / p[1] * (times_cut - p[2])) + p[3]
                def errfunc(p):
                    return prob[:times_cut_index] - fitfunc(p)
                out = leastsq(errfunc, np.array([np.max(prob), period_fit[i], times[np.argmax(prob)], np.max(prob), 0]), full_output=1)
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
                axes[2].set_title("No enough available points.")
                print(f"No enough available points. Please resweep once again or enlarge sweep range.")
            else:
                #----------- Third round fit ------------#
                axes[2].plot(freq, amps, 'bo', label="exp")
                amp_max = np.max(amps)
                fmin_guess = np.mean(freq)
                p0_guess = (amps[0] - amp_max) / (freq[0] - fmin_guess)**2
                p1_guess = (amps[-1] - amp_max) / (freq[-1] - fmin_guess)**2
                p_guess = np.array([p0_guess, p1_guess, fmin_guess, amp_max])
                def fitfunc(p, xs):
                    return np.heaviside(p[2] - xs, 0) * p[0] * (xs - p[2])**2 + p[3] + np.heaviside(xs - p[2], 0) * p[1] * (xs - p[2])**2
                def errfunc(p):
                    return amps - fitfunc(p, freq)
                out = leastsq(errfunc, p_guess)
                p = out[0]
                axes[2].plot(freq, fitfunc(p, freq), 'k-', label="fit")
                axes[2].legend()
                if p[2] > freq[-1] or p[2] < freq[0] or p[0] > 0 or p[1] > 0:
                    print("You should probably enlarge your sweep range. The optimial point is not in the current range.")
                    axes[2].set_title(f"Optimal point not found ")
                    # self.result.set_not_found()
                    self.opt_freq,self.opt_cz = 0,0
                else:
                    #----------- Fourth round fit ------------#
                    id_opt = np.argmax(fitfunc(p, freq))
                    id_left = (id_opt - 3) if (id_opt - 3) > 0 else 0
                    id_right = (id_opt + 4) if (id_opt + 4) < len(freq) else len(freq)
                    xs = freq[id_left : id_right]
                    p_guess = [p0_guess, freq[id_opt], amps[id_opt]]
                    def fitfunc(p, xs):
                        return p[0] * (p[1] - xs)**2 + p[2]
                    #----------- find max amplitude ----------#
                    def errfunc(p):
                        return amps[id_left: id_right] - fitfunc(p, xs)
                    out = leastsq(errfunc, p_guess)
                    p = out[0]
                    axes[2].plot(xs, fitfunc(p, xs), 'm--', label="fine-fit")
                    freq_fit = np.linspace(xs[0], xs[-1], 100)
                    data_fit = fitfunc(p, freq_fit)
                    f_opt = freq_fit[np.argmax(data_fit)]
                    id_max = np.argmax(amps)
                    if np.max(data_fit) < np.max(amps) and (id_left <= id_max <= id_right):
                        f_opt = freq[id_max]
                        gate_time = period_fit[id_max]
                        print("We use the raw measured data.")
                    else:
                        #---------- fit gate time ----------------#
                        def errfunc(p):
                            return period_fit[id_left: id_right] - fitfunc(p, xs)
                        p0_guess =  (period_fit[id_left] -  period_fit[id_opt])/ (freq[id_left] - freq[id_opt])**2
                        p_guess = [p0_guess, freq[id_opt], period_fit[id_opt]]
                        out = leastsq(errfunc, p_guess)
                        gate_time = fitfunc(out[0], f_opt)
                    #---------- show final result ------------#
                    axes[2].vlines(f_opt, np.min(amps), np.max(amps), 'g', linestyle='--', linewidth=1.5)
                    axes[2].set_title(f"The optimal frequency is {f_opt}.")
                    # self.result.set_result((f_opt, gate_time))
                    result, result_add = self.result.get_result()
                    print(f_opt, gate_time)
                    self.opt_freq = f_opt * 1e6
                    self.opt_cz = gate_time / 1e9
        except:
            print("Something wrong with the fitting process.")
            self.opt_freq,self.opt_cz = 0,0
        fig.show()
        return [self.opt_freq , self.opt_cz ]

    def plotter(self, axis):

        datarray = self.dataset[f'y{self.qubit}']
        qubit = self.qubit
        datarray.plot(ax=axis, x=f'cz_pulse_frequencies_sweep{qubit}',cmap='RdBu_r')
        # fig = axis.pcolormesh(amp,freq,magnitudes,shading='nearest',cmap='RdBu_r')
        axis.scatter(self.opt_freq,self.opt_cz,c='r',label = 'CZ Duration = {:.1f} ns'.format(self.opt_cz*1e9),marker='X',s=200,edgecolors='k', linewidth=1.5,zorder=10)
        # plt.scatter(opt_swap,opt_freq,c='b',label = 'SWAP12 Duration= {:.2f} V'.format(opt_swap),marker='X',s=200,edgecolors='k', linewidth=1.5,zorder=10)
        axis.vlines(self.opt_freq,self.amp[0],self.amp[-1],label = 'Frequency Detuning = {:.2f} MHz'.format(self.opt_freq/1e6),colors='k',linestyles='--',linewidth=1.5)
        axis.hlines(self.opt_cz,self.freq[0],self.freq[-1],colors='k',linestyles='--',linewidth=1.5)
        # axis.legend(loc = 'lower center', bbox_to_anchor=(-0.15, -0.36, 1.4, .102), mode='expand', ncol=2,
        #             title = 'Optimal Gate Parameters', columnspacing=200,borderpad=1)
        # cbar = plt.colorbar(fig)
        # cbar.set_label('|2>-state Population', labelpad=10)
        axis.set_xlim([self.freq[0],self.freq[-1]])
        axis.set_ylim([self.amp[0],self.amp[-1]])
        axis.set_ylabel('Parametric Drive Durations (s)')
        axis.set_xlabel('Frequency Detuning (Hz)')
        axis.set_title(f'CZ Chevron - Qubit {self.qubit[1:]}')

        # self.fig.show()
        # if self.result.status != SweepResultStatus.FOUND:
        #     print("Not found optimal parameters.")
        # else:
        #     opt_freq, self.opt_cz = self.result.get_result()
        #     self.opt_freq = opt_freq[1]
        #     datarray = self.dataset[f'y{self.qubit}']
        #     qubit = self.qubit
        #     datarray.plot(ax=axis, x=f'cz_pulse_durations{qubit}',cmap='RdBu_r')
        #     # # fig = axis.pcolormesh(amp,freq,magnitudes,shading='nearest',cmap='RdBu_r')
        #     axis.scatter(
        #         self.opt_cz,self.opt_freq,
        #         c='r',
        #         label = 'CZ Duration = {:.1f} ns'.format(self.opt_cz*1e9),
        #         marker='X',s=150,
        #         edgecolors='k', linewidth=1.0,zorder=10
        #     )
        #     # plt.scatter(opt_swap,opt_freq,c='b',label = 'SWAP12 Duration= {:.2f} V'.format(opt_swap),marker='X',s=200,edgecolors='k', linewidth=1.5,zorder=10)
        #     axis.hlines(
        #         self.opt_freq,self.amp[0],
        #         self.amp[-1],
        #         label = 'Frequency Detuning = {:.2f} MHz'.format(self.opt_freq/1e6),
        #         colors='k',
        #         linestyles='--',
        #         linewidth=1.5
        #     )
        #     axis.vlines(self.opt_cz,self.freq[0],self.freq[-1],colors='k',linestyles='--',linewidth=1.5)
        #     axis.legend(loc = 'lower center', bbox_to_anchor=(-0.15, -0.36, 1.4, .102), mode='expand', ncol=2,
        #                 title = 'Optimal Gate Parameters', columnspacing=200,borderpad=1)
        #     # # cbar = plt.colorbar(fig)
        #     # # cbar.set_label('|2>-state Population', labelpad=10)
        #     # axis.set_ylim([self.freq[0],self.freq[-1]])
        #     # axis.set_ylim([self.amp[0],self.amp[-1]])
        #     axis.set_xlabel('Parametric Drive Durations (s)')
        #     axis.set_ylabel('Frequency Detuning (Hz)')