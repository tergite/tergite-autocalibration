from analysis.resonator_spectroscopy_analysis import ResonatorSpectroscopyAnalysis
from analysis.qubit_spectroscopy_analysis import QubitSpectroscopyAnalysis
from quantify_core.data.handling import set_datadir
# from quantify_analysis import qubit_spectroscopy_analysis, rabi_analysis, T1_analysis, XY_crosstalk_analysis, ramsey_analysis, SSRO_analysis
# from quantify_core.analysis.calibration import rotate_to_calibrated_axis
import matplotlib.patches as mpatches
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import redis
set_datadir('.')

redis_connection = redis.Redis(decode_responses=True)


class BaseAnalysis():
    def __init__(self, result_dataset: xr.Dataset):
       self.result_dataset = result_dataset

       self.n_vars = len(self.result_dataset.data_vars)
       self.n_coords = len(self.result_dataset.coords)
       self.fit_numpoints = 300
       self.column_grid = 3
       self.rows = (self.n_vars + 2) // self.column_grid

       self.node_result = {}
       self.fig, self.axs = plt.subplots(
            nrows=self.rows, ncols=np.min((self.n_coords, self.column_grid)), squeeze=False
        )
       self.qoi = 0 # quantity of interest

    def update_redis_trusted_values(self,node:str, this_qubit:str,transmon_parameter:str):
        print(f'\n--------> {transmon_parameter} = { self.qoi }<--------\n')
        redis_connection.hset(f"transmons:{this_qubit}",f"{transmon_parameter}",self.qoi)
        redis_connection.hset(f"cs:{this_qubit}",node,'calibrated')
        self.node_result.update({this_qubit: self.qoi})

class Multiplexed_Resonator_Spectroscopy_Analysis(BaseAnalysis):
    def __init__(self, result_dataset: xr.Dataset, node: str):
        super().__init__(result_dataset)
        for indx, var in enumerate(result_dataset.data_vars):
            this_qubit = result_dataset[var].attrs['qubit']
            ds = result_dataset[var].to_dataset()
            fitted_resonator_frequency = ResonatorSpectroscopyAnalysis(dataset=ds)
            fitted_resonator_frequency.run_fitting()
            fitting_results = fitted_resonator_frequency.fit_results
            fitting_model = fitting_results['hanger_func_complex_SI']
            fit_result = fitting_model.values

            fitted_resonator_frequency = fit_fr = fit_result['fr']
            fit_Ql = fit_result['Ql']
            fit_Qe = fit_result['Qe']
            fit_ph = fit_result['theta']
            # print(f'{ fit_Ql = }')

            minimum_freq = fit_fr / (4*fit_Qe*fit_Ql*np.sin(fit_ph)) * (
                            4*fit_Qe*fit_Ql*np.sin(fit_ph)
                          - 2*fit_Qe*np.cos(fit_ph)
                          + fit_Ql
                          + np.sqrt(  4*fit_Qe**2
                                    - 4*fit_Qe*fit_Ql*np.cos(fit_ph)
                                    + fit_Ql**2 )
                          )

            self.qoi = minimum_freq
            # PLOT THE FIT -- ONLY FOR S21 MAGNITUDE
            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
            fitting_model.plot_fit(this_axis,numpoints = self.fit_numpoints,xlabel=None, title=None)
            this_axis.axvline(minimum_freq,c='blue',ls='solid',label='frequency at min')
            this_axis.axvline(fitted_resonator_frequency,c='magenta',ls='dotted',label='fitted frequency')
            # this_axis.set_title(f'{node} for {this_qubit}')


            self.update_redis_trusted_values(node, this_qubit,'ro_freq')

            handles, labels = this_axis.get_legend_handles_labels()
            patch = mpatches.Patch(color='red', label=f'{this_qubit}')
            handles.append(patch)
            this_axis.set(title=None)
            this_axis.legend(handles=handles)


class Multiplexed_Two_Tones_Spectroscopy_Analysis(BaseAnalysis):
    def __init__(self, result_dataset: xr.Dataset, node: str):
        super().__init__(result_dataset)
        for indx, var in enumerate(result_dataset.data_vars):
            this_qubit = result_dataset[var].attrs['qubit']
            ds = result_dataset[var].to_dataset()

            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
            # this_axis.set_title(f'{node_name} for {this_qubit}')
            qubit_spec_analysis = QubitSpectroscopyAnalysis(ds)
            rough_qubit_frequency = qubit_spec_analysis.run_fitting()

            self.qoi = rough_qubit_frequency

            qubit_spec_analysis.plotter(this_axis)

            self.update_redis_trusted_values(node, this_qubit,'freq_01')

            hasPeak=qubit_spec_analysis.has_peak()
            handles, labels = this_axis.get_legend_handles_labels()
            patch = mpatches.Patch(color='red', label=f'{this_qubit}')
            patch2 = mpatches.Patch(color='blue', label=f'Peak Found:{hasPeak}')
            handles.append(patch)
            handles.append(patch2)
            this_axis.set(title=None)
            this_axis.legend(handles=handles)
