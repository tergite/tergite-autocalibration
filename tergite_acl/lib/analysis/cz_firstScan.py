from tergite_acl.lib.analysis_base import BaseAnalysis
import xarray as xr
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import chi2 as chi2dist
from tergite_acl.lib.analysis.cz_firstScanResult import CZFirstScanResult,FitResultStatus

class CZFirstScan(BaseAnalysis):
        
    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        self.dataset = dataset
        self.data_var = list(dataset.data_vars.keys())[0]
        self.qubit = dataset[self.data_var].attrs['qubit']
        self.status = FitResultStatus.NOT_AVAILABLE

    def fitfunc(self, x, *p):
        if len(p) < 4:
            print(p)
            raise ValueError("Insufficient parameters for fitting")
        
        return p[0] * np.cos(2 * np.pi / p[1] * (x - p[2])) + p[3]    
    
    def run_fitting(self) -> CZFirstScanResult:
        freq = self.dataset[f'cz_pulse_frequencies_sweep{self.qubit}'].values  # MHz
        times = self.dataset[f'cz_pulse_durations{self.qubit}'].values  # ns

        freq = freq / 1e6
        times = times * 1e9
        magnitudes = np.array([[np.linalg.norm(u) for u in v] for v in self.dataset[f'y{self.qubit}']])
        magnitudes = np.transpose((magnitudes - np.min(magnitudes)) / (np.max(magnitudes) - np.min(magnitudes)))

        print("First fit")
        # Here we could reintroduce the fft for better estumate of inital period        
        paras_fit = []
        chi2 = []
        pvalues = []
        for i, prob in enumerate(magnitudes):
            print(i)
            errors = np.full(len(prob), 0.05)
            initial_parameters = [0.4, 100, times[np.argmax(prob)], 0.5]
            bounds = ([0.01, 20, min(times), -1], [0.6, 400, max(times), 1])

            try:
                popt = curve_fit(self.fitfunc, times, prob, sigma=errors, bounds=bounds, p0=initial_parameters)
            except RuntimeError as e:
                print("An error occurred during curve fitting:", e)
                self.status = FitResultStatus.NOT_FOUND
                r = CZFirstScanResult(pvalues, paras_fit, self.status)    
                return r
            
            params = popt[0]
            # Calculate the residuals
            residuals = prob - self.fitfunc(times, *params)

            # Calculate the reduced chi-square statistic
            chi_sq = np.sum((residuals/errors) ** 2) / (len(prob) - len(params))

            # Calculate the p-value
            p_value = 1 - chi2dist.cdf(chi_sq, len(prob) - len(params))

            paras_fit.append(params)
            chi2.append(chi_sq)
            pvalues.append(p_value)

        for i, prob in enumerate(magnitudes):
            period_fit = paras_fit[i][1]
            times_cut_index = np.argmin(np.abs(times - 3 * period_fit))
            times_cut = times[:times_cut_index]
            prob_cut = prob[:times_cut_index]
            #print(times_cut)
            if len(times_cut) > 5: 
                
                errors = np.full(len(prob_cut), 0.05)
                initial_parameters = [0.4, 100, times[np.argmax(prob_cut)], 0.5]
                bounds = ([0.2, 20, min(times_cut), -1], [0.6, 400, max(times_cut), 1])
                
                try:
                    popt = curve_fit(self.fitfunc, times_cut, prob_cut, sigma=errors, bounds=bounds, p0=initial_parameters)
                except RuntimeError as e:
                    print("An error occurred during curve fitting:", e)
                    self.status = FitResultStatus.NOT_FOUND
                    r = CZFirstScanResult(pvalues, paras_fit, self.status)    
                    return r
                
                params = popt[0]
                # Calculate the residuals
                residuals = prob_cut - self.fitfunc(times_cut, *params)

                # Calculate the reduced chi-square statistic
                chi_sq = np.sum((residuals/errors[:times_cut_index]) ** 2) / (len(prob_cut) - len(params))

                # Calculate the p-value
                p_value = 1 - chi2dist.cdf(chi_sq, len(prob_cut) - len(params))

                print("pvalue: " + str(p_value))

                paras_fit[i] = params
                chi2[i] = chi_sq
                pvalues[i] = p_value
            else:
                print("Not enough points, using first step")
        
        self.status = FitResultStatus.FOUND
        r = CZFirstScanResult(pvalues, paras_fit, self.status)
        return r

    def plotter(self, axis):
        print("plot")