"""
Module containing classes that model, fit and plot data from a Rabi experiment.
"""
import numpy as np
import lmfit
import xarray as xr

def exponential_decay_function( x: float, amplitude: float, B: float, offset: float) -> float:
    return amplitude * np.exp(-x / B) + offset


class ExpDecayModel(lmfit.model.Model):
    """
    Generate an exponential decay model that can be fit to randomized benchmarking data.
    """
    def __init__(self, *args, **kwargs):

        super().__init__(exponential_decay_function, *args, **kwargs)

        self.set_param_hint("amplitude", vary=True)
        self.set_param_hint("B", vary=True, min=0)
        self.set_param_hint("offset", vary=True)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        x = kws.get("x", None)

        if x is None:
            return None

        amplitude_guess= data[0]-data[-1]
        self.set_param_hint("amplitude", value=amplitude_guess)

        offset_guess = data[-1]
        self.set_param_hint("offset", value=offset_guess)

        B_guess = (x[-1]+x[0])/2
        self.set_param_hint("B", value=B_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)



class RandomizedBenchmarkingAnalysis():
    """
    Analysis that fits an exponential decay function to randomized benchmarking data.
    """
    def  __init__(self,dataset: xr.Dataset):
        self.data_var = list(dataset.data_vars.keys())[0]
        self.qubit = dataset[self.data_var].attrs['qubit']
        self.S21 = dataset[self.data_var]
        for coord in dataset[self.data_var].coords:
            if 'cliffords' in coord: self.number_cliffords_coord = coord
            elif 'repetitions' in coord: self.repetitions_coord = coord
        self.number_of_repetitions = dataset.dims[self.repetitions_coord]
        self.number_of_cliffords = dataset[self.number_cliffords_coord].values
        self.normalized_data_dict = {}
        for repetition_index in range(self.number_of_repetitions):
            complex_values = self.S21.isel(
                {self.repetitions_coord: [repetition_index]}
            )
            measurements = complex_values.values.flatten()
            data = measurements[:-2]
            calibration_0 = measurements[-2]
            calibration_1 = measurements[-1]
            displacement_vector = calibration_1 - calibration_0
            data_translated_to_zero = data - calibration_0

            rotation_angle = np.angle(displacement_vector)
            rotated_data = data_translated_to_zero * np.exp( -1j * rotation_angle)
            rotated_0 = calibration_0 * np.exp(-1j * rotation_angle)
            rotated_1 = calibration_1 * np.exp(-1j * rotation_angle)
            normalization = (rotated_1 - rotated_0).real
            real_rotated_data = rotated_data.real
            self.normalized_data_dict[repetition_index] = real_rotated_data / normalization

        self.fit_results = {}

    def run_fitting(self):
        # model = ExpDecayModel()
        #
        # translated_to_zero_samples = self.S21 - self.calibration_point_0
        # rotated_samples = translated_to_zero_samples * np.exp(-1j * self.rotation_angle)
        # normalized_rotated_samples = rotated_samples / self.normalization
        #
        # self.magnitudes = np.abs(normalized_rotated_samples)
        # n_cliffords = self.independents
        #
        # # Normalize data to interval [0,1]
        # # self.normalized_magnitudes = (self.magnitudes-self.magnitudes[0])/(self.magnitudes[1]-self.magnitudes[0])
        #
        # # Gives an initial guess for the model parameters and then fits the model to the data.
        # guess = model.guess(data=self.magnitudes[2:], x=n_cliffords[2:])
        # fit_result = model.fit(self.magnitudes, params=guess, x=n_cliffords)
        #
        # self.fit_n_cliffords = np.linspace( n_cliffords[0], n_cliffords[-1], 400)
        # self.fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_n_cliffords})
        # self.normalized_fit_y = (self.fit_y-self.magnitudes[0])/(self.magnitudes[1]-self.magnitudes[0])
        # #print(f'{ fit_result.params= }')
        return [0]

    def plotter(self,ax):
        for repetition_index in range(self.number_of_repetitions):
            real_values = self.normalized_data_dict[repetition_index]
            ax.plot(self.number_of_cliffords[:-2], real_values)
            # ax.axhline(magnitudes[-2],c='b')
            # ax.axhline(magnitudes[-1],c='r')
        ax.set_ylabel(f'|S21| (V)')
        ax.grid()
