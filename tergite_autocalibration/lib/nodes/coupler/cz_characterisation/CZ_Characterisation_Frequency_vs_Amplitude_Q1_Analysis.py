import numpy as np
import xarray as xr
from tergite_autocalibration.lib.nodes.coupler.cz_characterisation.CZ_Characterisation_Frequency_vs_Amplitude_Analysis import CZ_Characterisation_Frequency_vs_Amplitude_Analysis

class CZ_Characterisation_Frequency_vs_Amplitude_Q1_Analysis(CZ_Characterisation_Frequency_vs_Amplitude_Analysis):
    def __init__(self, dataset: xr.Dataset):
        super().__init__(dataset)
        self.data_var = list(dataset.data_vars.keys())[0]
        self.S21 = dataset[self.data_var].values
        self.fit_results = {}
        self.qubit = dataset[self.data_var].attrs["qubit"]
        dataset[f"y{self.qubit}"].values = np.abs(self.S21)
        self.dataset = dataset

    def run_fitting(self) -> list[float, float]:
        print("WARNING TESTING CZ FREQUeNCY AND AMPLITUDE Q1 ANALYSIS")
        return self.run_fitting_find_max()

    def run_fitting_find_max(self):
        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                frequencies_coord = coord
            elif "amplitudes" in coord:
                amplitudes_coord = coord
        self.freqs = self.dataset[frequencies_coord].values / 1e6  # MHz
        self.amps = self.dataset[amplitudes_coord].values  # bias

        magnitudes = np.array(
            [[np.linalg.norm(u) for u in v] for v in self.dataset[f"y{self.qubit}"]]
        )
        magnitudes = np.transpose(
            (magnitudes - np.max(magnitudes))
            / (np.max(magnitudes) - np.max(magnitudes))
        )
        max_index = np.argmax(magnitudes)
        max_index = np.unravel_index(max_index, magnitudes.shape)
        self.opt_freq = self.freqs[max_index[0]]
        self.opt_amp = self.amps[max_index[1]]
        print(self.opt_freq, self.opt_amp)
        return [self.opt_freq, self.opt_amp]

