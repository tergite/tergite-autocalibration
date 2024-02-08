"""
Module containing classes that model, fit and plot data from a Rabi experiment.
"""
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
import xarray as xr

class StateDiscriminationAnalysis():
    """
    Analysis that fits a cosine function to Rabi oscillation data.
    """
    def  __init__(self,dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.I = self.S21.real
        self.Q = self.S21.imag
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']

    def run_fitting(self):
        y = self.independents
        IQ = np.array([self.I, self.Q]).T
        lda = LinearDiscriminantAnalysis(solver = "svd", store_covariance=True)

        # Save the LDA model, datapoints and states
        # if self.qubit == 'q25':
        #     with open(f'state-disc-q25.disc', 'wb') as f:
        #         pickle.dump(lda, f, protocol=pickle.HIGHEST_PROTOCOL)
        #         f.close()

        # run the discrimination, y_classified are the classified levels
        y_classified = lda.fit(IQ,y).predict(IQ)

        tp = y == y_classified # True Positive
        tp0 = tp[y == 0] # true positive levels when sending 0
        tp1 = tp[y == 1] # true positive levels when sending 1
        tp2 = tp[y == 2] # true positive levels when sending 2

        IQ0 = IQ[y == 0] # IQ when sending 0
        IQ1 = IQ[y == 1] # IQ when sending 1
        IQ2 = IQ[y == 2] # IQ when sending 2

        IQ0_tp = IQ0[ tp0] # True Positive when sending 0
        IQ0_fp = IQ0[~tp0]
        IQ1_tp = IQ1[ tp1] # True Positive when sending 1
        IQ1_fp = IQ1[~tp1]
        IQ2_tp = IQ2[ tp2] # True Positive when sending 2
        IQ2_fp = IQ2[~tp2]

        self.IQ0_positives = [IQ0_tp,IQ0_fp]
        self.IQ1_positives = [IQ1_tp,IQ1_fp]
        self.IQ2_positives = [IQ2_tp,IQ2_fp]

        return [0]

    def plotter(self,ax):
        IQ0_tp, IQ0_fp = self.IQ0_positives
        IQ1_tp, IQ1_fp = self.IQ1_positives
        IQ2_tp, IQ2_fp = self.IQ2_positives

        err_wr_0 = len(IQ0_fp) / (len(IQ0_fp) + len(IQ0_tp))
        err_wr_1 = len(IQ1_fp) / (len(IQ1_fp) + len(IQ1_tp))
        # When reading 0 , dots are correct and crosses are in error
        mark_size = 40
        ax.scatter(IQ0_tp[:, 0], IQ0_tp[:, 1], marker=".", s=mark_size, color="red", label='send 0 and read 0')
        ax.scatter(IQ0_fp[:, 0], IQ0_fp[:, 1], marker="x", s=mark_size, color="orange",
                label=f'errors when sending |0>: {err_wr_0:.4f}'
                )
        # When reading 1 , dots are correct and crosses are in error
        ax.scatter(IQ1_tp[:, 0], IQ1_tp[:, 1], marker=".", s=mark_size, color="blue", label='send 1 and read 1')
        ax.scatter(IQ1_fp[:, 0], IQ1_fp[:, 1], marker="x", s=mark_size, color="dodgerblue",
                label=f'errors when sending |1>: {err_wr_1:.4f}'
                )
        # When reading 2 , dots are correct and crosses are in error
        ax.scatter(IQ2_tp[:, 0], IQ2_tp[:, 1], marker=".", s=mark_size, color="green")
        ax.scatter(IQ2_fp[:, 0], IQ2_fp[:, 1], marker="x", s=mark_size, color="lime",
                # label=f'errors when sending |2>: {err_wr_2:.4f}'
                )


        ax.set_title(f'State Discrimination for {self.qubit}')
        ax.set_xlabel('I (V)')
        ax.set_ylabel('Q (V)')
        ax.legend(fontsize='xx-small')
        ax.grid()
