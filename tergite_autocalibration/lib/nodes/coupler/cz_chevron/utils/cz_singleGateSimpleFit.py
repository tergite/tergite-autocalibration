from tergite_autocalibration.config.settings import PLOTTING
from tergite_autocalibration.lib.base.analysis import BaseAnalysis
import xarray as xr
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import chi2 as chi2dist
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.utils.cz_singleGateSimpleFitResult import (
    CZSingleGateSimpleFitResult,
    FitResultStatus,
)
import matplotlib.pyplot as plt


class CZSingleGateSimpleFit(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset, frequencies, durations):
        super().__init__()
        self.dataset = dataset
        # print(dataset)
        self.data_var = list(dataset.data_vars.keys())[0]
        # print(self.data_var)
        self.qubit = dataset[self.data_var].attrs["qubit"]
        self.result = CZSingleGateSimpleFitResult()
        self.fittefTimes = []
        self.freq = frequencies
        self.times = durations
        self.magnitudes = []
        self.paras_fit = []
        self.chi2 = []
        self.pvalues = []
        self.start_Amps = []
        self.start_periods = []
        self.errors = []

    def get_dataarray_by_partial_name(self, dataset_path, partial_name):
        with xr.open_dataset(dataset_path) as ds:
            for var_name in ds.data_vars:
                if partial_name in var_name:
                    return ds[var_name]

    def fitfunc(self, x, *p):
        if len(p) < 4:
            print(p)
            raise ValueError("Insufficient parameters for fitting")

        return p[0] * np.cos(2 * np.pi / p[1] * (x - p[2])) + p[3]

    def run_fitting(self) -> CZSingleGateSimpleFitResult:
        magnitudes = np.array(
            [[np.linalg.norm(u) for u in v] for v in self.dataset[f"y{self.qubit}"]]
        )
        self.magnitudes = np.transpose(
            (magnitudes - np.min(magnitudes))
            / (np.max(magnitudes) - np.min(magnitudes))
        )

        # Here we could reintroduce the fft for better estumate of inital period
        self.errors = self.SetInitialValues()

        # print("First fit")
        status = self.FirstFit()

        # Second fit in limited range
        if status != FitResultStatus.NOT_FOUND:
            status = self.SecondFit()

        self.result = CZSingleGateSimpleFitResult(self.pvalues, self.paras_fit, status)
        return self.result

    def SetInitialValues(self):
        for i, prob in enumerate(self.magnitudes):
            # print(f'freqIndex: {i}')
            indexMax = np.argmax(prob)
            indexMin = np.argmin(prob)
            startPeriod = abs(self.times[indexMax] - self.times[indexMin]) * 2
            if startPeriod < 30 or startPeriod > 500:
                # print(f'Per: {startPeriod}')
                startPeriod = 100
            self.start_periods.append(startPeriod)
            startAmp = (max(prob) - min(prob)) / 2
            self.start_Amps.append(startAmp)
            # print(f'Amp: {startAmp}')
            error = max(prob) / 20  # 0.05
            errors = np.full(len(prob), error)
        return errors

    def FirstFit(self):
        for i, prob in enumerate(self.magnitudes):
            initial_parameters = [
                self.start_Amps[i],
                self.start_periods[i],
                self.times[np.argmax(prob)],
                0.5,
            ]
            bounds = (
                [0.01, 20, min(self.times), -1],
                [0.6, 800, max(self.times) * 2, 1],
            )

            try:
                popt = curve_fit(
                    self.fitfunc,
                    self.times,
                    prob,
                    sigma=self.errors,
                    bounds=bounds,
                    p0=initial_parameters,
                )
            except RuntimeError as e:
                print("An error occurred during curve fitting:", e)
                return FitResultStatus.NOT_FOUND

            params = popt[0]
            # Calculate the residuals
            residuals = prob - self.fitfunc(self.times, *params)

            # Calculate the reduced chi-square statistic
            chi_sq = np.sum((residuals / self.errors) ** 2) / (len(prob) - len(params))

            # Calculate the p-value
            p_value = 1 - chi2dist.cdf(chi_sq, len(prob) - len(params))

            self.paras_fit.append(params)
            self.chi2.append(chi_sq)
            self.pvalues.append(p_value)
            self.fittefTimes.append(self.times)

        return FitResultStatus.FOUND

    def SecondFit(self):
        for i, prob in enumerate(self.magnitudes):
            # print(i)
            period_fit = self.paras_fit[i][1]
            times_cut_index = np.argmin(np.abs(self.times - 4 * period_fit))
            times_cut = self.times[:times_cut_index]
            prob_cut = prob[:times_cut_index]
            # print(times_cut)
            if len(times_cut) < 6:
                print("Not enough points, using first step")
            else:
                errors_cut = self.errors[:times_cut_index]
                amp_step2_init = self.paras_fit[i][0]
                if amp_step2_init < 0.2:
                    amp_step2_init = 0.25
                if amp_step2_init > 0.6:
                    amp_step2_init = 0.55

                period_step2_init = self.paras_fit[i][1]
                if period_step2_init < 20:
                    period_step2_init = 250
                if period_step2_init > 600:
                    period_step2_init = 250

                initial_parameters = [
                    amp_step2_init,
                    period_step2_init,
                    self.times[np.argmax(times_cut)],
                    0.5,
                ]
                bounds = (
                    [0.2, 20, min(times_cut), -1],
                    [0.6, 600, max(times_cut) * 2, 1],
                )

                try:
                    popt = curve_fit(
                        self.fitfunc,
                        times_cut,
                        prob_cut,
                        sigma=errors_cut,
                        bounds=bounds,
                        p0=initial_parameters,
                    )
                except RuntimeError as e:
                    print("An error occurred during curve fitting:", e)
                    return FitResultStatus.NOT_FOUND

                params = popt[0]
                # Calculate the residuals
                residuals = prob_cut - self.fitfunc(times_cut, *params)

                # Calculate the reduced chi-square statistic
                chi_sq = np.sum((residuals / self.errors[:times_cut_index]) ** 2) / (
                    len(prob_cut) - len(params)
                )

                # Calculate the p-value
                p_value = 1 - chi2dist.cdf(chi_sq, len(prob_cut) - len(params))
                # print("pvalue: " + str(p_value))

                self.paras_fit[i] = params
                self.chi2[i] = chi_sq
                self.pvalues[i] = p_value
                self.fittefTimes[i] = times_cut

        return FitResultStatus.FOUND

    def plotter(self, outputFolder):
        fig, axes = plt.subplots(1, 3, figsize=(15, 7), num=1)
        sc = axes[0].imshow(
            self.magnitudes,
            aspect="auto",
            cmap="jet",
            extent=[self.times[0], self.times[-1], self.freq[-1], self.freq[0]],
        )

        plt.colorbar(sc)
        axes[0].set_xlabel("Times [ns]")
        axes[0].set_ylabel("Frequency [GHz]")
        axes[0].set_xlim(self.times[0], self.times[-1])
        axes[0].set_ylim(self.freq[-1], self.freq[0])

        for i, prob in enumerate(self.magnitudes):

            def fitfunc(p, x):
                return p[0] * np.cos(2 * np.pi / p[1] * (x - p[2])) + p[3]

            # if self.paras_fit[i][0] < 0.21 or self.paras_fit[i][0] > 1 or self.paras_fit[i][1] > 200 or self.paras_fit[i][1] < 20:
            x_high_res = np.linspace(
                self.fittefTimes[i][0], self.fittefTimes[i][-1], 100
            )
            color_palette = plt.cm.tab10.colors
            color = color_palette[i % len(color_palette)]
            if self.result.pvalues[i] < 0.99:
                axes[1].set_xlabel("Times [ns]")
                axes[1].set_ylabel("Amplitude")
                axes[1].plot(self.times, prob, "o", markersize=5, color=color)
                axes[1].plot(
                    x_high_res,
                    fitfunc(self.result.fittedParams[i], x_high_res),
                    "-.",
                    linewidth=1,
                    color=color,
                )
            else:
                axes[2].set_xlabel("Times [ns]")
                axes[2].plot(self.times, prob, "o", markersize=5, color=color)
                axes[2].plot(
                    x_high_res,
                    fitfunc(self.result.fittedParams[i], x_high_res),
                    "-.",
                    linewidth=1,
                    color=color,
                )

        if PLOTTING:
            plt.show()
            plt.pause(3)
        fig.savefig(f"{outputFolder}/SummaryScan_{self.qubit}.png")
        plt.close()

        num_plots = len(self.magnitudes)
        num_rows = (
            num_plots + 2
        ) // 3  # Calculate the number of rows needed for the subplot grid

        figAll, axesAll = plt.subplots(num_rows, 3, figsize=(15, 5 * num_rows), num=2)
        for i, prob in enumerate(self.magnitudes):

            def fitfunc(p, x):
                return p[0] * np.cos(2 * np.pi / p[1] * (x - p[2])) + p[3]

            row = i // 3  # Calculate the row index
            col = i % 3  # Calculate the column index

            axesAll[row, col].plot(
                self.times,
                prob,
                "o",
                markersize=5,
                label=f"P-val: {self.result.pvalues[i]:.4g} \n p[0] = {self.result.fittedParams[i][0]:.4g} p[1] = {self.result.fittedParams[i][1]:.4g}\n p[2] = {self.result.fittedParams[i][2]:.4g} p[3] = {self.result.fittedParams[i][3]:.4g}",
            )

            x_high_res = np.linspace(
                self.fittefTimes[i][0], self.fittefTimes[i][-1], 100
            )
            axesAll[row, col].plot(
                x_high_res,
                fitfunc(self.result.fittedParams[i], x_high_res),
                "-.",
                linewidth=1,
            )

            axesAll[row, col].set_xlabel("Times [ns]")
            axesAll[row, col].set_ylabel("Amplitude")
            axesAll[row, col].legend(loc="upper right")

        if PLOTTING:
            plt.show()
        figAll.savefig(f"{outputFolder}/AllFits_{self.qubit}.png")
        plt.close(figAll)
        plt.close("all")
