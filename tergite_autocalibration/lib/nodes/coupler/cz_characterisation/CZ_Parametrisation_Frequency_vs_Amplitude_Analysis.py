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

    def plotter(self, outputFolder):
        fig, ax = plt.subplots(figsize=(15, 7), num=1)

        datarray = self.dataset[f"y{self.qubit}"]

        # Plot the data array on the single plot
        datarray.plot(ax=ax, cmap="RdBu_r")

        # Scatter plot and lines on the same plot
        ax.scatter(
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
        ax.vlines(
            self.opt_freq,
            self.amplitudes[0],
            self.amplitudes[-1],
            label="Frequency Detuning = {:.2f} MHz".format(self.opt_freq / 1e6),
            colors="k",
            linestyles="--",
            linewidth=1.5,
        )
        ax.hlines(
            self.opt_amp,
            self.frequencies[0],
            self.frequencies[-1],
            colors="k",
            linestyles="--",
            linewidth=1.5,
        )

        ax.set_xlim([self.frequencies[0], self.frequencies[-1]])
        ax.set_ylim([self.amplitudes[0], self.amplitudes[-1]])
        ax.set_ylabel("Parametric Drive amplitude (V)")
        ax.set_xlabel("Frequency Detuning (Hz)")
        ax.set_title(f"CZ - Qubit {self.qubit[1:]}")
        ax.legend()  # Add legend to the plot

        plt.show()
        fig.savefig(f"{outputFolder}/Frequancy_Amplitude_{self.qubit}.png")
        plt.pause(3)
        plt.close()