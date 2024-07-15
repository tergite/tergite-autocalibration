from pyexpat import model
import lmfit
from matplotlib.axes import Axes
import numpy as np
import xarray as xr

from ....base.analysis import BaseAnalysis

# Exponential decay function used for modeling
def exponential_decay_function(m: float, p: float, A: float, B: float) -> float:
    return A * p**m + B

class ExpDecayModel(lmfit.model.Model):
    """
    Generate an exponential decay model that can be fit to purity benchmarking data.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(exponential_decay_function, *args, **kwargs)
        
        # Set parameter hints for the fitting process
        self.set_param_hint("A", vary=True)
        self.set_param_hint("B", vary=True, min=0)
        self.set_param_hint("p", vary=True, min=0)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        # Generate initial guesses for the model parameters based on the data
        m = kws.get("m", None)
        
        if m is None:
            return None
        amplitude_guess = data[0] - data[-1]
        self.set_param_hint("A", value=amplitude_guess)

        offset_guess = data[-1]
        self.set_param_hint("B", value=offset_guess)

        p_guess = 0.95
        self.set_param_hint("p", value=p_guess)

        # Create and return the parameters object with initial guesses
        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)

class PurityBenchmarkingAnalysis(BaseAnalysis):
    """
    Analysis that fits an exponential decay function to purity benchmarking data.
    """
    
    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        # Extract the primary data variable and qubit information from the dataset
        self.data_var = list(dataset.data_vars.keys())[0]
        self.qubit = dataset[self.data_var].attrs["qubit"]
        self.purity = dataset[self.data_var]

        # Identify and store the coordinates related to the number of Cliffords and seed
        for coord in dataset[self.data_var].coords:
            if "cliffords" in coord:
                self.number_cliffords_coord = coord
            elif "seed" in coord:
                self.seed_coord = coord

        # Extract the number of repetitions and the sequence lengths for Cliffords
        self.number_of_repetitions = dataset.dims[self.seed_coord]
        self.number_of_cliffords = dataset[self.number_cliffords_coord].values
        self.number_of_cliffords_runs = dataset.dims[self.number_cliffords_coord] - 3
        self.normalized_data_dict = {}

        # Store calibration points
        self.calibration_points = {
            "ground": [],
            "excited": [],
            "second_excited": []
        }
        
        # Normalize purity data for each repetition
        for repetition_index in range(self.number_of_repetitions):
            measurements = self.purity.isel({self.seed_coord: [repetition_index]}).values.flatten()
            data = measurements[:-3]  # Extract data points excluding calibration points
            calibration_0 = measurements[-3]  # Calibration point 0
            calibration_1 = measurements[-2]  # Calibration point 1
            calibration_2 = measurements[-1]  # Calibration point 2

            displacement_vector = calibration_1 - calibration_0  # Calculate displacement vector
            data_translated_to_zero = data - calibration_0  # Translate data to zero reference
            rotation_angle = np.angle(displacement_vector)  # Calculate rotation angle
            rotated_data = data_translated_to_zero * np.exp(-1j * rotation_angle)  # Rotate data
            rotated_0 = calibration_0 * np.exp(-1j * rotation_angle)  # Rotate calibration point 0
            rotated_1 = calibration_1 * np.exp(-1j * rotation_angle)  # Rotate calibration point 1
            rotated_2 = calibration_2 * np.exp(-1j * rotation_angle)  # Rotate calibration point 2
            normalization = (rotated_1 - rotated_0).real  # Calculate normalization factor
            real_rotated_data = rotated_data.real  # Extract real part of rotated data
            self.normalized_data_dict[repetition_index] = real_rotated_data / normalization  # Store normalized data

        self.fit_results = {}  # Dictionary to store fitting results


    def run_fitting(self):
        # Calculate the purity from the normalized data
        purity_results = {}
        for repetition_index in range(self.number_of_repetitions):
            x_value = self.normalized_data_dict[repetition_index]["X"]
            y_value = self.normalized_data_dict[repetition_index]["Y"]
            z_value = self.normalized_data_dict[repetition_index]["Z"]
            x_exp = 1 - x_value
            y_exp = 1 - y_value
            z_exp = 1 - z_value
            purity = x_exp**2 + y_exp**2 + z_exp**2
            purity_results[repetition_index] = purity
            
        # Sum and average the normalized purity across all repetitions
        sum_purity = np.sum([purity for purity in purity_results.values()], axis=0)
        avg_purity = sum_purity / len(purity_results)

        # Initialize the exponential decay model
        model = ExpDecayModel()

        n_cliffords = self.number_of_cliffords[:-3]

        # Generate initial parameter guesses and fit the model to the data
        guess = model.guess(data=avg_purity, m=n_cliffords)
        fit_result = model.fit(avg_purity, params=guess, m=n_cliffords)

        # Generate fitted values for plotting
        self.fit_n_cliffords = np.linspace(n_cliffords[0], n_cliffords[-1], 400)
        self.fit_y = model.eval(
            fit_result.params, **{model.independent_vars[0]: self.fit_n_cliffords}
        )
        self.fidelity = fit_result.params["p"].value

        # Store fit results and report
        self.fit_results = fit_result
        self.fit_report = fit_result.fit_report()

        # Return the fitted parameter for fidelity
        return [self.fidelity]

    def plotter(self, ax: Axes):
        # Plot normalized data for each repetition with low transparency
        for repetition_index in range(self.number_of_repetitions):
            real_values = self.normalized_data_dict[repetition_index]["X"]
            ax.plot(self.number_of_cliffords[:-3], real_values, alpha=0.2)
            ax.annotate(
                f"{repetition_index}",
                (self.number_of_cliffords[:-3][-1], real_values[-1]),
            )

        # Plot the fitted curve, summed data, and add labels
        ax.plot(
            self.fit_n_cliffords,
            self.fit_y,
            "ro-",
            lw=2.5,
            label=f"p = {self.fidelity:.3f}",
        )
        ax.plot(self.number_of_cliffords[:-3], self.fit_results.best_fit, ls="dashed", c="black")
        ax.set_ylabel("Purity")
        ax.set_xlabel("Number of Cliffords")
        ax.grid()
