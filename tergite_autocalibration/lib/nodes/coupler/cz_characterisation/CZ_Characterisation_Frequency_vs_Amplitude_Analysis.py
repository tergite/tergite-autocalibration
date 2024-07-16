import numpy as np
import xarray as xr
from tergite_autocalibration.lib.base.analysis import BaseAnalysis

class CZ_Characterisation_Frequency_vs_Amplitude_Analysis(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        self.data_var = list(dataset.data_vars.keys())[0]
        self.S21 = dataset[self.data_var].values
        self.fit_results = {}
        self.qubit = dataset[self.data_var].attrs["qubit"]
        dataset[f"y{self.qubit}"].values = np.abs(self.S21)
        self.dataset = dataset

    def plotter(self, axis):
        datarray = self.dataset[f"y{self.qubit}"]
        datarray.plot(ax=axis, cmap="RdBu_r")
        axis.scatter(
            self.opt_freq,
            self.opt_amp,
            c="r",
            label="CZ Amplitude = {:.3f} V".format(self.opt_amp),
            marker="X",
            s=200,
            edgecolors="k",
            linewidth=1.5,
            zorder=10,
        )
        axis.vlines(
            self.opt_freq,
            self.amps[0],
            self.amps[-1],
            label="Frequency Detuning = {:.2f} MHz".format(self.opt_freq / 1e6),
            colors="k",
            linestyles="--",
            linewidth=1.5,
        )
        axis.hlines(
            self.opt_amp,
            self.freqs[0],
            self.freqs[-1],
            colors="k",
            linestyles="--",
            linewidth=1.5,
        )

        axis.set_xlim([self.freqs[0], self.freqs[-1]])
        axis.set_ylim([self.amps[0], self.amps[-1]])
        axis.set_ylabel("Parametric Drive amplitude (V)")
        axis.set_xlabel("Frequency Detuning (Hz)")
        axis.set_title(f"CZ - Qubit {self.qubit[1:]}")
