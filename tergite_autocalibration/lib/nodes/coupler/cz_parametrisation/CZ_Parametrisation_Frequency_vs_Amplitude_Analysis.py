from matplotlib import pyplot as plt
import numpy as np
import xarray as xr
from tergite_autocalibration.lib.base.analysis import BaseAnalysis

class CZ_Parametrisation_Frequency_vs_Amplitude_Analysis(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset, freqs, amps):
        super().__init__()
        self.data_var = list(dataset.data_vars.keys())[0]
        self.S21 = dataset[self.data_var].values
        self.qubit = dataset[self.data_var].attrs["qubit"]
        dataset[f"y{self.qubit}"].values = np.abs(self.S21)
        self.dataset = dataset
        self.frequencies = freqs
        self.amplitudes = amps
        self.opt_freq = -1
        self.opt_amp = -1

    def plotter(self, axis: plt.Axes):
        datarray = self.dataset[f"y{self.qubit}"]

        if datarray.size == 0:
            raise ValueError(f"Data array for qubit {self.qubit} is empty.")
        
        # Plot the data array on the single plot
        datarray.plot(ax=axis, cmap="RdBu_r")
        #datarray.plot(ax=axis, x=f"cz_pulse_frequencies_sweep{self.qubit}", cmap="RdBu_r")
        # Scatter plot and lines on the same plot
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
            self.amplitudes[0],
            self.amplitudes[-1],
            label="Frequency Detuning = {:.2f} MHz".format(self.opt_freq / 1e6),
            colors="k",
            linestyles="--",
            linewidth=1.5,
        )
        axis.hlines(
            self.opt_amp,
            self.frequencies[0],
            self.frequencies[-1],
            colors="k",
            linestyles="--",
            linewidth=1.5,
        )

        axis.set_xlim([self.frequencies[0], self.frequencies[-1]])
        axis.set_ylim([self.amplitudes[0], self.amplitudes[-1]])
        axis.set_ylabel("Parametric Drive amplitude (V)")
        axis.set_xlabel("Frequency Detuning (Hz)")
        axis.set_title(f"CZ - Qubit {self.qubit[1:]}")
        axis.legend()  # Add legend to the plot

