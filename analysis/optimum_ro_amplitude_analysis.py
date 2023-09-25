"""
Module containing a class that fits data from a resonator spectroscopy experiment.
"""
import numpy as np
import redis
import xarray as xr
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
redis_connection = redis.Redis(decode_responses=True)

class OptimalROAmplitudeAnalysis():
    """
    Analysis that  extracts the optimal RO amplitude.
    """
    def __init__(self, dataset: xr.Dataset):
        self.dataset = dataset
        self.qubit = dataset.attrs['qubit']
        self.data_var = list(dataset.data_vars.keys())[0]

        for coord in dataset.coords:
            if 'amplitudes' in str(coord):
                self.amplitude_coord = coord
            elif 'state' in str(coord):
                self.state_coord = coord
        self.independents = dataset[self.state_coord].values
        self.amplitudes = dataset.coords[self.amplitude_coord]
        self.fit_results = {}

    def run_fitting(self):
        self.fidelities = []
        for indx, ro_amplitude in enumerate(self.amplitudes):
            y = self.independents
            IQ_complex = self.dataset[self.data_var].isel({self.amplitude_coord:[indx]})
            I = IQ_complex.values.real.flatten()
            Q = IQ_complex.values.imag.flatten()
            IQ = np.array([I,Q]).T
            lda = LinearDiscriminantAnalysis(solver = "svd", store_covariance=True)
            y_pred = lda.fit(IQ,y).predict(IQ)

            tp = y == y_pred # True Positive
            tp0 = tp[y == 0] # true positive levels when reading 0
            tp1 = tp[y == 1] # true positive levels when reading 1
            tp2 = tp[y == 2] # true positive levels when reading 2

            IQ0 = IQ[y == 0] # IQ when reading 0
            IQ1 = IQ[y == 1] # IQ when reading 1
            IQ2 = IQ[y == 2] # IQ when reading 2

            IQ0_tp = IQ0[ tp0] # True Positive when sending 0
            IQ0_fp = IQ0[~tp0]
            IQ1_tp = IQ1[ tp1] # True Positive when sending 1
            IQ1_fp = IQ1[~tp1]
            IQ2_tp = IQ2[ tp2] # True Positive when sending 2
            IQ2_fp = IQ2[~tp2]

            err_wr_0 = len(IQ0_fp) / (len(IQ0_fp) + len(IQ0_tp))
            err_wr_1 = len(IQ1_fp) / (len(IQ1_fp) + len(IQ1_tp))

            assignment = 1 - 1/2 * (err_wr_0 + err_wr_1)
            self.fidelities.append(assignment)

        self.optimal_amplitude = 0
        return self.optimal_amplitude

    def plotter(self,ax):
        this_qubit = self.dataset.attrs['qubit']
        ax.set_xlabel('RO amplitude')
        ax.set_ylabel('assignment fidelity')
        ax.plot(self.amplitudes, self.fidelities)

        ax.grid()
