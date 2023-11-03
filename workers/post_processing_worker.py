'''Analyze the measured dataset and extract the qoi (quantity of interest)'''
import collections
import matplotlib.pyplot as plt
import xarray as xr
from analysis.motzoi_analysis import MotzoiAnalysis
from analysis.n_rabi_analysis import NRabiAnalysis
from analysis.cz_chevron_analysis import CZChevronAnalysis
from analysis.cz_calibration_analysis import CZCalibrationAnalysis
from analysis.resonator_spectroscopy_analysis import ResonatorSpectroscopyAnalysis, ResonatorSpectroscopy_1_Analysis, ResonatorSpectroscopy_2_Analysis
from analysis.qubit_spectroscopy_analysis import QubitSpectroscopyAnalysis
from analysis.qubit_spectroscopy_multidim import QubitSpectroscopyMultidim
from analysis.optimum_ro_frequency_analysis import (
    OptimalROFrequencyAnalysis,
    OptimalRO_012_FrequencyAnalysis
)
from analysis.optimum_ro_amplitude_analysis import OptimalROAmplitudeAnalysis
from analysis.state_discrimination_analysis import StateDiscrimination
from analysis.rabi_analysis import RabiAnalysis
from analysis.punchout_analysis import PunchoutAnalysis
from analysis.ramsey_analysis import RamseyAnalysis
from analysis.tof_analysis import analyze_tof
from analysis.T1_analysis import T1Analysis
from quantify_core.data.handling import set_datadir
# from quantify_core.analysis.calibration import rotate_to_calibrated_axis
import matplotlib.patches as mpatches
import numpy as np
from logger.tac_logger import logger

import matplotlib
matplotlib.use('tkagg')
import redis
set_datadir('.')
redis_connection = redis.Redis(decode_responses=True)

def post_process(result_dataset: xr.Dataset, node: str, data_path: str):
    analysis = Multiplexed_Analysis(result_dataset, node, data_path)

    # figure_manager = plt.get_current_fig_manager()
    # figure_manager.window.showMaximized()
    fig = plt.gcf()
    fig.set_tight_layout(True)
    fig.savefig(f'{data_path}/{node}.png', bbox_inches='tight', dpi=600)
    plt.show(block=False)
    plt.pause(30)
    plt.close()

    if node != 'tof':
        analysis.node_result.update({'measurement_dataset':result_dataset.to_dict()})


class BaseAnalysis():
    def __init__(self, result_dataset: xr.Dataset, data_path: str):
       self.result_dataset = result_dataset
       self.data_path = data_path

       self.n_vars = len(self.result_dataset.data_vars)
       self.n_coords = len(self.result_dataset.coords)
       self.fit_numpoints = 300
       self.column_grid = 3
       self.rows = (self.n_vars + 2) // self.column_grid

       self.node_result = {}
       self.fig, self.axs = plt.subplots(
            nrows=self.rows, ncols=np.min((self.n_coords, self.column_grid)), squeeze=False,figsize=(self.column_grid*5,self.rows*5)
        )
       self.qoi = 0 # quantity of interest

    def update_redis_trusted_values(self,node:str, this_qubit:str,transmon_parameter:str):
        redis_connection.hset(f"transmons:{this_qubit}",f"{transmon_parameter}",self.qoi)
        redis_connection.hset(f"cs:{this_qubit}",node,'calibrated')
        self.node_result.update({this_qubit: self.qoi})


class Multiplexed_Analysis(BaseAnalysis):
    def __init__(self, result_dataset: xr.Dataset, node: str, data_path: str):
        if node == 'tof':
            tof = analyze_tof(result_dataset, True)
            return

        super().__init__(result_dataset, data_path)
        data_vars_dict = collections.defaultdict(set)
        for var in result_dataset.data_vars:
            this_qubit = result_dataset[var].attrs['qubit']
            data_vars_dict[this_qubit].add(var)

        for indx, var in enumerate(result_dataset.data_vars):
            this_qubit = result_dataset[var].attrs['qubit']
            # ds = result_dataset[var].to_dataset()
            ds = xr.Dataset()
            for var in data_vars_dict[this_qubit]:
                ds = xr.merge([ds,result_dataset[var]])

            ds.attrs['qubit'] = this_qubit
            # breakpoint()

            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
            kw_args = {}
            # this_axis.set_title(f'{node_name} for {this_qubit}')

            if node == 'resonator_spectroscopy':
                analysis_class = ResonatorSpectroscopyAnalysis
                redis_field = 'ro_freq'
            elif node == 'qubit_01_spectroscopy_pulsed':
                analysis_class = QubitSpectroscopyAnalysis
                redis_field = 'freq_01'
            elif node == 'rabi_oscillations':
                analysis_class = RabiAnalysis
                redis_field = 'mw_amp180'
            elif node == 'ramsey_correction':
                analysis_class = RamseyAnalysis
                redis_field = 'freq_01'
            elif node == 'motzoi_parameter':
                analysis_class = MotzoiAnalysis
                redis_field = 'mw_motzoi'
            elif node == 'n_rabi_oscillations':
                analysis_class = NRabiAnalysis
                redis_field = 'mw_amp180'
            elif node == 'resonator_spectroscopy_1':
                analysis_class = ResonatorSpectroscopy_1_Analysis
                redis_field = 'ro_freq_1'
            elif node == 'T1':
                analysis_class = T1Analysis
                redis_field = 't1_time'
            elif node == 'two_tone_multidim':
                analysis_class = QubitSpectroscopyMultidim
                redis_field = 'freq_01'
            elif node == 'qubit_12_spectroscopy_pulsed':
                analysis_class = QubitSpectroscopyAnalysis
                redis_field = 'freq_12'
            elif node == 'rabi_oscillations_12':
                analysis_class = RabiAnalysis
                redis_field = 'mw_ef_amp180'
            elif node == 'ramsey_correction_12':
                analysis_class = RamseyAnalysis
                redis_field = 'freq_12'
                kw_args = {'redis_field': redis_field}
            elif node == 'resonator_spectroscopy_2':
                analysis_class = ResonatorSpectroscopy_2_Analysis
                redis_field = 'ro_freq_2'
            elif node == 'ro_frequency_optimization':
                analysis_class = OptimalROFrequencyAnalysis
                redis_field = 'ro_freq_opt'
            elif node == 'ro_frequency_optimization_gef':
                analysis_class = OptimalRO_012_FrequencyAnalysis
                redis_field = 'ro_freq_opt'
            elif node == 'ro_amplitude_optimization':
                analysis_class = OptimalROAmplitudeAnalysis
                redis_field = 'ro_pulse_amp_opt'
            elif node == 'punchout':
                analysis_class = PunchoutAnalysis
                redis_field = 'ro_amp'
            elif node == 'state_discrimination':
                analysis_class = StateDiscrimination
                redis_field = 'discrimimator'
            elif node == 'cz_chevron':
                analysis_class = CZChevronAnalysis
                redis_field = 'cz_pulse_frequency'
            elif node == 'cz_calibration':
                analysis_class = CZCalibrationAnalysis
                redis_field = 'cz_pulse_amplitude'
            else:
                raise ValueError(f'Invalid node: {node}')

            node_analysis = analysis_class(ds, **kw_args)
            self.qoi = node_analysis.run_fitting()

            node_analysis.plotter(this_axis)

            self.update_redis_trusted_values(node, this_qubit,redis_field)

            handles, labels = this_axis.get_legend_handles_labels()
            #if node == 'qubit_01_spectroscopy_pulsed':
            #    hasPeak=node_analysis.has_peak()
            #    patch2 = mpatches.Patch(color='blue', label=f'Peak Found:{hasPeak}')
            #    handles.append(patch2)
            if node == 'T1':
                T1_micros = self.qoi*1e6
                patch2 = mpatches.Patch(color='blue', label=f'T1 = {T1_micros:.2f}')
                handles.append(patch2)
            patch = mpatches.Patch(color='red', label=f'{this_qubit}')
            handles.append(patch)
            this_axis.set(title=None)
            this_axis.legend(handles=handles)
            # logger.info(f'Analysis for the {node} of {this_qubit} is done, saved at {self.data_path}')

#class Multiplexed_Punchout_Analysis(BaseAnalysis):
#    def __init__(self, result_dataset: xr.Dataset, node: str):
#        super().__init__(result_dataset)
#        for indx, var in enumerate(result_dataset.data_vars):
#            this_qubit = result_dataset[var].attrs['qubit']
#            ds = result_dataset[var].to_dataset()
#            #breakpoint()
#
#            N_amplitudes = ds.dims[f'ro_amplitudes{this_qubit}']
#            # print(f'{ N_amplitudes = }')
#            # norm_factors = np.array([max(ds.y0[ampl].values) for ampl in range(N_amplitudes)])
#            # ds[f'y{this_qubit}'] = ds.y0 / norm_factors[:,None]
#            raw_values = np.abs(ds[f'y{this_qubit}'].values)
#            normalized_values = raw_values / raw_values.max(axis=0)
#            ds[f'y{this_qubit}'].values = normalized_values
#
#            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
#
#            ds[f'y{this_qubit}'].plot(x=f'ro_frequencies{this_qubit}', ax=this_axis)
#            # this_axis.set_title(f'{node_name} for {this_qubit}')
#
#            handles, labels = this_axis.get_legend_handles_labels()
#            patch = mpatches.Patch(color='red', label=f'{this_qubit}')
#            handles.append(patch)
#            this_axis.set(title=None)
#            this_axis.legend(handles=handles)
