"""
Module containing classes that model, fit, and plot data from a purity benchmarking experiment.
"""
import lmfit
import numpy as np
import xarray as xr
from matplotlib.axes import Axes

from ....base.analysis import BaseAnalysis


def exponential_decay_function(m: float, p: float, A: float, B: float) -> float:
    return A * p**m + B


class ExpDecayModel(lmfit.model.Model):
    """
    Generate an exponential decay model that can be fit to purity benchmarking data.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(exponential_decay_function, *args, **kwargs)

        self.set_param_hint("A", vary=True)
        self.set_param_hint("B", vary=True, min=0)
        self.set_param_hint("p", vary=True, min=0)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        m = kws.get("m", None)
        
        if m is None:
            return None
        amplitude_guess = data[0] - data[-1]
        self.set_param_hint("A", value=amplitude_guess)

        offset_guess = data[-1]
        self.set_param_hint("B", value=offset_guess)

        p_guess = 0.95
        self.set_param_hint("p", value=p_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


class PurityBenchmarkingAnalysis(BaseAnalysis):
    """
    Analysis that fits an exponential decay function to purity benchmarking data.
    """
    
    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        self.data_var = list(dataset.data_vars.keys())[0]
        self.qubit = dataset[self.data_var].attrs["qubit"]
        self.purity = dataset[self.data_var]
        for coord in dataset[self.data_var].coords:
            if "cliffords" in coord:
                self.number_cliffords_coord = coord
            elif "seed" in coord:
                self.seed_coord = coord
        self.number_of_repetitions = dataset.dims[self.seed_coord]
        self.number_of_cliffords = dataset[self.number_cliffords_coord].values
        self.number_of_cliffords_runs = dataset.dims[self.number_cliffords_coord] - 3
        self.normalized_data_dict = {}
        for repetition_index in range(self.number_of_repetitions):
            values = self.purity.isel({self.seed_coord: [repetition_index]}).values.flatten()
            data = values[:-3]

            # Normalization to make the initial value 1
            max_value = data[0]
            normalized_data = data / max_value

            self.normalized_data_dict[repetition_index] = normalized_data

        self.fit_results = {}

    def run_fitting(self):
        sum_data = np.sum([arr for arr in self.normalized_data_dict.values()], axis=0)
        self.sum = sum_data / len(self.normalized_data_dict)

        model = ExpDecayModel()

        n_cliffords = self.number_of_cliffords[:-3]

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(data=self.sum, m=n_cliffords)
        fit_result = model.fit(self.sum, params=guess, m=n_cliffords)

        self.fit_n_cliffords = np.linspace(n_cliffords[0], n_cliffords[-1], 400)
        self.fit_y = model.eval(
            fit_result.params, **{model.independent_vars[0]: self.fit_n_cliffords}
        )
        self.fidelity = fit_result.params["p"].value
        return [self.fidelity]

    def plotter(self, ax: Axes):
        for repetition_index in range(self.number_of_repetitions):
            real_values = self.normalized_data_dict[repetition_index]
            ax.plot(self.number_of_cliffords[:-3], real_values, alpha=0.2)
            ax.annotate(
                f"{repetition_index}",
                (self.number_of_cliffords[:-3][-1], real_values[-1]),
            )

        ax.plot(
            self.fit_n_cliffords,
            self.fit_y,
            "ro-",
            lw=2.5,
            label=f"p = {self.fidelity:.3f}",
        )
        ax.plot(self.number_of_cliffords[:-3], self.sum, ls="dashed", c="black")
        ax.set_ylabel("Normalized Purity")
        ax.set_xlabel("Number of Cliffords")
        ax.grid()