from quantify_core.analysis.spectroscopy_analysis import ResonatorSpectroscopyAnalysis
from quantify_core.data.handling import set_datadir
# from quantify_analysis import qubit_spectroscopy_analysis, rabi_analysis, T1_analysis, XY_crosstalk_analysis, ramsey_analysis, SSRO_analysis
from quantify_core.analysis.calibration import rotate_to_calibrated_axis
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
import matplotlib.patches as mpatches
import numpy as np
from scipy.optimize import curve_fit
import xarray as xr
import scipy
import matplotlib.pyplot as plt
import json
import re
import redis
import joblib
set_datadir('.')

redis_connection = redis.Redis(decode_responses=True)

def _from_coord_to_dataset( coord: str, full_dataset: xr.Dataset ) -> xr.Dataset:
    qubit = full_dataset[coord].long_name
    attrs = full_dataset.attrs
    try:
        match = re.search(r'^q\d+',qubit)
        assert match
    except :
        print(f'{qubit} is not named correctly')

    partial_ds = xr.Dataset(coords = { 'x0' : ('dim_0',full_dataset[coord].values,
                               full_dataset[coord].attrs)},
                             attrs = { **attrs , **{'qubit_name':qubit} } )

    for var in full_dataset.data_vars:
        if full_dataset[var].long_name == qubit:
            if full_dataset[var].attrs['name'] == 'magn' or full_dataset[var].attrs['name'] == 'I':
                partial_ds['y0'] = ('dim_0', full_dataset[var].data, full_dataset[var].attrs)
            elif full_dataset[var].attrs['name'] == 'phase' or full_dataset[var].attrs['name'] == 'Q':
                partial_ds['y1'] = ('dim_0', full_dataset[var].data, full_dataset[var].attrs)
    return partial_ds


def _from_qubit_to_dataset(qubit:str, full_dataset:xr.Dataset) -> xr.Dataset:
   # qubit = full_dataset[coord].long_name[:2]
   attrs = full_dataset.attrs
   try:
       match = re.search(r'^q\d+',qubit)
       assert match
   except :
       print(f'{qubit} is not named correctly')

   dimensions = attrs['dimensions'].replace("'", "\"")
   dimensions = json.loads(dimensions)
   # we reverse the tuples since the 'unpacking' happens in reverse order than the data 'packing'
   dimensions_keys = tuple(reversed(tuple(dimensions.keys())))
   dimensions_tuple = tuple(reversed(tuple(dimensions.values())))
   ''' construct the coordinates dictionary.
   The initial coordinate values are a big two dimensional mesh with D1*D2*...*Dn elements.
   For each coordinate we slice the initial big mesh.
   '''
   coord_dictionary = {}
   for x_coord in full_dataset.coords:
       coord_values = full_dataset[x_coord].values.reshape( dimensions_tuple )
       if full_dataset[x_coord].long_name == qubit:
           coord_name = full_dataset[x_coord].attrs['name']

           # this is for sweeping hardware parameters, because you can't set the name.
           # so we make sure that the parameter name is substring of the hardware parameter name
           # TODO properly attach hardware params onto TransmonElement
           for dim_key in dimensions_keys: #hardware hack
               if dim_key in coord_name:
                   coord_name = dim_key

           coord_slicing = [ slice(0,None)
                   if  list(dimensions_keys).index(coord_name) == current_index
                   else 0 for current_index, _ in enumerate(dimensions_keys)]

           coord_dictionary[coord_name] = coord_values[tuple(coord_slicing)]

   # Initialize the partial dataset with the coordinates
   partial_ds = xr.Dataset(coords=coord_dictionary)
   # ensure int for single shots
   if 'state_level' in partial_ds:
       partial_ds = partial_ds.assign({'state_level': np.int64(partial_ds.state_level + 1e-2)})

   for var in full_dataset.data_vars:
       if full_dataset[var].attrs['name'] == 'magn' and full_dataset[var].long_name == qubit:
           values = full_dataset[var].values.reshape(dimensions_tuple)
           partial_ds['y0'] = (dimensions_keys, values, full_dataset[var].attrs)
       elif full_dataset[var].attrs['name'] == 'I' and full_dataset[var].long_name == qubit:
           values = full_dataset[var].values.reshape(dimensions_tuple)
           partial_ds['y0'] = (dimensions_keys, values, full_dataset[var].attrs)
       elif full_dataset[var].attrs['name'] == 'Q' and full_dataset[var].long_name == qubit:
           values = full_dataset[var].values.reshape(dimensions_tuple)
           partial_ds['y1'] = (dimensions_keys, values, full_dataset[var].attrs)

   return partial_ds


class BaseAnalysis():
    def __init__(self, result_dataset: xr.Dataset):
       self.result_dataset = result_dataset
       attrs = result_dataset.attrs
       dimensions = attrs['dimensions'].replace("'", "\"")
       dimensions = json.loads(dimensions)
       unique_coordinates = len(dimensions)
       if unique_coordinates != 0:
           self.n_coords = len( result_dataset.coords ) // unique_coordinates
       else :
           self.n_coords = len( result_dataset.coords )

       var_counter = 0
       for var in result_dataset.data_vars:
           IQ_type = result_dataset.data_vars[var].attrs['name']
           if IQ_type == 'magn' or IQ_type == 'I':
               var_counter += 1
       self.n_vars = var_counter
       # self.n_vars = 2 # for motzoi TODO
       self.fit_numpoints = 300
       self.column_grid = 3
       self.rows = (self.n_vars + 2) // self.column_grid
       print(f'{ self.rows = }')

       self.node_result = dict()
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
    def __init__(self,result_dataset,node_name):
        super().__init__(result_dataset)
        for indx, this_coord in enumerate(result_dataset.coords):
            ds = _from_coord_to_dataset(this_coord, result_dataset)
            this_qubit = ds.attrs['qubit_name']
            fitted_resonator_frequency = ResonatorSpectroscopyAnalysis(dataset=ds)
            fitted_resonator_frequency.process_data()
            fitted_resonator_frequency.run_fitting()
            fitted_resonator_frequency.analyze_fit_results()
            # fitted_resonator_frequency.create_figures()
            # fitted_resonator_frequency.display_figs_mpl()
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
            # this_axis.set_title(f'{node_name} for {this_qubit}')
            latex = '' # Todo

            print(f'\n-------->{ fitted_resonator_frequency = }<--------\n')

            if node_name == 'resonator_frequency' or node_name == 'resonator_spectroscopy_NCO':
                self.update_redis_trusted_values(node_name, this_qubit,'ro_freq')
            if node_name == 'resonator_frequency_1' or node_name == 'resonator_spectroscopy_1_NCO':
                self.update_redis_trusted_values(node_name, this_qubit,'ro_freq_1')
            if node_name == 'resonator_frequency_2' or node_name == 'resonator_spectroscopy_2_NCO':
                self.update_redis_trusted_values(node_name, this_qubit,'ro_freq_2')

            if node_name == 'resonator_frequency_1' or node_name == 'resonator_spectroscopy_1_NCO':
               res_freq_0 = float(redis_connection.hget(f"transmons:{this_qubit}","ro_freq"))
               this_axis.axvline(res_freq_0,lw=3,c='green',ls='dashed',label='qubit at $|0\\rangle$')
            if node_name == 'resonator_frequency_2' or node_name == 'resonator_spectroscopy_2_NCO':
               res_freq_0 = float(redis_connection.hget(f"transmons:{this_qubit}","ro_freq"))
               res_freq_1 = float(redis_connection.hget(f"transmons:{this_qubit}","ro_freq_1"))
               this_axis.axvline(res_freq_0,lw=3,c='green',ls='dashed',label='qubit at $|0\\rangle$')
               this_axis.axvline(res_freq_1,lw=3,c='lightgreen',ls='dotted',label='qubit at $|1\\rangle$')

            handles, labels = this_axis.get_legend_handles_labels()
            patch = mpatches.Patch(color='red', label=f'{this_qubit}')
            handles.append(patch)
            this_axis.set(title=None)
            this_axis.legend(handles=handles)



#class Multiplexed_Two_Tones_Spectroscopy_Analysis(BaseAnalysis):
#    def __init__(self,result_dataset,node_name):
#        super().__init__(result_dataset)
#        for indx, this_coord in enumerate(result_dataset.coords):
#            ds = _from_coord_to_dataset(this_coord, result_dataset)
#            this_qubit = ds.attrs['qubit_name']
#            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
#            # this_axis.set_title(f'{node_name} for {this_qubit}')
#            qubit_spec_result = qubit_spectroscopy_analysis.QubitSpectroscopyAnalysis(ds)
#            rough_qubit_frequency = qubit_spec_result.model_fit()
#
#            self.qoi = rough_qubit_frequency
#            latex = ''
#
#            qubit_spec_result.plotter(this_axis)
#
#            if node_name == 'qubit_2tn_frequency' or node_name == 'qubit_01_spectroscopy_pulsed_NCO':
#               self.update_redis_trusted_values(node_name, this_qubit,'freq_01',latex)
#               print('UPDATING FREQ01' )
#            if node_name == 'f12_2tn_frequency' or node_name == 'qubit_12_spectroscopy_pulsed_NCO':
#               print('UPDATING FREQ12' )
#               self.update_redis_trusted_values(node_name, this_qubit,'freq_12',latex)
#               freq_01 = float(redis_connection.hget(f"transmons:{this_qubit}","freq_01"))
#               anharmonicity = rough_qubit_frequency - freq_01
#               print(f'{ anharmonicity = }')
#               redis_connection.hset(f"transmons:{this_qubit}","anharmonicity",anharmonicity)
#
#            hasPeak=qubit_spectroscopy_analysis.has_peak(ds.y0.values)
#            handles, labels = this_axis.get_legend_handles_labels()
#            patch = mpatches.Patch(color='red', label=f'{this_qubit}')
#            patch2 = mpatches.Patch(color='blue', label=f'Peak Found:{hasPeak}')
#            handles.append(patch)
#            handles.append(patch2)
#            this_axis.set(title=None)
#            this_axis.legend(handles=handles)
#
#
#class Multiplexed_Rabi_Oscillations_Analysis(BaseAnalysis):
#    def __init__(self,result_dataset,node_name):
#        super().__init__(result_dataset)
#        for indx, this_coord in enumerate(result_dataset.coords):
#            ds = _from_coord_to_dataset(this_coord, result_dataset)
#
#            this_qubit = ds.attrs['qubit_name']
#            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
#            # this_axis.set_title(f'{node_name} for {this_qubit}')
#            rabi_result = rabi_analysis.RabiAnalysis(ds)
#            pi_pulse_amplitude = rabi_result.model_fit()
#
#            self.qoi = pi_pulse_amplitude
#            print(f'{ node_name = }')
#            latex = ''
#
#            rabi_result.plotter(this_axis)
#
#            handles, labels = this_axis.get_legend_handles_labels()
#            patch = mpatches.Patch(color='red', label=f'{this_qubit}')
#            handles.append(patch)
#            this_axis.set(title=None)
#            this_axis.legend(handles=handles)
#
#            if node_name == 'rabi_frequency' or node_name == 'rabi_oscillations_BATCHED':
#                self.update_redis_trusted_values(node_name, this_qubit,'mw_amp180',latex)
#            if node_name == 'rabi_12_frequency' or node_name == 'rabi_oscillations_12_BATCHED':
#                self.update_redis_trusted_values(node_name, this_qubit,'mw_ef_amp180',latex)
#
#        self.node_result.update({'measurement_dataset':result_dataset.to_dict()})
#
#class Multiplexed_T1_Analysis(BaseAnalysis):
#    def __init__(self,result_dataset,node_name):
#        super().__init__(result_dataset)
#        for indx, this_coord in enumerate(result_dataset.coords):
#            ds = _from_coord_to_dataset(this_coord, result_dataset)
#
#            this_qubit = ds.attrs['qubit_name']
#            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
#            # this_axis.set_title(f'{node_name} for {this_qubit}')
#            T1_result = T1_analysis.T1Analysis(ds)
#            T1_time = T1_result.model_fit()
#            T1_micros=T1_time*1e6
#
#            self.qoi = T1_time
#            print(f'{ node_name = }')
#            latex = ''
#
#            T1_result.plotter(this_axis)
#
#            handles, labels = this_axis.get_legend_handles_labels()
#            patch = mpatches.Patch(color='red', label=f'{this_qubit}')
#            handles.append(patch)
#            patch2=mpatches.Patch(color='green', label=f'{T1_micros} μs')
#            handles.append(patch2)
#            this_axis.set(title=None)
#            this_axis.legend(handles=handles)
#
#            #if node_name == 'rabi_frequency' or node_name == 'rabi_oscillations_BATCHED':
#            #    self.update_redis_trusted_values(node_name, this_qubit,'mw_amp180',latex)
#            #if node_name == 'rabi_12_frequency' or node_name == 'rabi_oscillations_12_BATCHED':
#            #    self.update_redis_trusted_values(node_name, this_qubit,'mw_ef_amp180',latex)
#
#        self.node_result.update({'measurement_dataset':result_dataset.to_dict()})
#
#class Crosstalk_Analysis(BaseAnalysis):
#    def __init__(self,result_dataset,node_name):
#        super().__init__(result_dataset)
#        for indx, this_coord in enumerate(result_dataset.coords):
#            ds = _from_coord_to_dataset(this_coord, result_dataset)
#
#            this_qubit = ds.attrs['qubit_name']
#            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
#            # this_axis.set_title(f'{node_name} for {this_qubit}')
#            XY_crosstalk_result = XY_crosstalk_analysis.XY_Crosstalk_Analysis(ds)
#            #T1_time = T1_result.model_fit()
#            #T1_micros=T1_time*1e6
#
#
#
#            #change all of this
#            #self.qoi = T1_time
#            print(f'{ node_name = }')
#            latex = ''
#
#            T1_result.plotter(this_axis)
#
#            handles, labels = this_axis.get_legend_handles_labels()
#            #patch = mpatches.Patch(color='red', label=f'{this_qubit}')
#            #handles.append(patch)
#            this_axis.set(title=None)
#            this_axis.legend(handles=handles)
#
#            #if node_name == 'rabi_frequency' or node_name == 'rabi_oscillations_BATCHED':
#            #    self.update_redis_trusted_values(node_name, this_qubit,'mw_amp180',latex)
#            #if node_name == 'rabi_12_frequency' or node_name == 'rabi_oscillations_12_BATCHED':
#            #    self.update_redis_trusted_values(node_name, this_qubit,'mw_ef_amp180',latex)
#
#        self.node_result.update({'measurement_dataset':result_dataset.to_dict()})
#
#class Multiplexed_RB_Analysis(BaseAnalysis):
#    def __init__(self,result_dataset,node_name):
#        super().__init__(result_dataset)
#        for indx, this_coord in enumerate(result_dataset.coords):
#            ds = _from_coord_to_dataset(this_coord, result_dataset)
#
#            this_qubit = ds.attrs['qubit_name']
#            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
#            # this_axis.set_title(f'{node_name} for {this_qubit}')
#
#            sequence_length = ds.x0.values[:-2]
#            I = ds.y0.values[:-2]
#            I_calib_0 = ds.y0.values[-2]
#            I_calib_1 = ds.y0.values[-1]
#            Q = ds.y1.values[:-2]
#            Q_calib_0 = ds.y1.values[-2]
#            Q_calib_1 = ds.y1.values[-1]
#            ref_0 = I_calib_0 + 1j*Q_calib_0
#            ref_1 = I_calib_1 + 1j*Q_calib_1
#            IQ = I + 1j*Q
#            rotated_IQ = rotate_to_calibrated_axis(IQ, ref_0, ref_1)
#
#            # Have an initial guess as to what the values of the parameters are
#            a_guess , b_guess , c_guess = 0.5 , 1-0.99 , 0.5
#
#            # Fit the function a * np.exp(b * t) + c to x and y
#            popt, pcov = curve_fit(
#                lambda t, a, b, c: a * np.exp(-b * t) + c,
#                sequence_length, rotated_IQ.real, p0=(a_guess, b_guess, c_guess)
#            )
#
#            a , b , c =  popt[0], popt[1], popt[2]
#            fidelity = np.exp(-b) + (1 - np.exp(-b))/2
#            print(f'{ fidelity = }')
#            self.qoi = fidelity
#            numpoints = np.linspace(sequence_length[0], sequence_length[-1], 300)
#            fitted = a * np.exp(-b * numpoints) + c
#
#            this_axis.plot(sequence_length, rotated_IQ.real, 'bo', label=f'{fidelity}')
#            this_axis.plot(numpoints, fitted, 'r-')
#            handles, labels = this_axis.get_legend_handles_labels()
#            patch = mpatches.Patch(color='red', label=f'{this_qubit}')
#            handles.append(patch)
#            this_axis.set(title=None)
#            this_axis.legend(handles=handles)
#
#            self.update_redis_trusted_values(node_name, this_qubit,'fidelity','')
#
#        self.node_result.update({'measurement_dataset':result_dataset.to_dict()})
#
#
#class Multiplexed_Ramsey_Analysis(BaseAnalysis):
#    def __init__(self,result_dataset,node_name):
#        super().__init__(result_dataset)
#        for indx, this_coord in enumerate(list(result_dataset.coords.keys())):
#            ds = _from_coord_to_dataset(this_coord, result_dataset)
#
#
#            this_qubit = ds.attrs['qubit_name']
#            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
#            # this_axis.set_title(f'{node_name} for {this_qubit}')
#
#            if node_name == 'ramsey_correction' or node_name == 'ramsey_correction_BATCHED':
#                this_transmon_param = 'freq_01'
#            elif node_name == 'ramsey_correction_12' or node_name == 'ramsey_correction_12_BATCHED':
#                this_transmon_param = 'freq_12'
#
#            rough_qubit_frequency = float(redis_connection.hget(f"transmons:{this_qubit}",this_transmon_param))
#            #TODO artificial_detuning is hardcoded
#            artificial_detuning = 3.0e6
#
#            ramsey_result = ramsey_analysis.RamseyAnalysis(ds,rough_qubit_frequency,artificial_detuning)
#
#            latex = ''
#
#            corrected_freq = ramsey_result.model_fit()
#            self.qoi = corrected_freq
#
#            ramsey_result.plotter(this_axis)
#            handles, labels = this_axis.get_legend_handles_labels()
#            patch = mpatches.Patch(color='red', label=f'{this_qubit}')
#            handles.append(patch)
#            this_axis.set(title=None)
#            this_axis.legend(handles=handles)
#
#            if node_name == 'ramsey_correction' or node_name == 'ramsey_correction_BATCHED':
#                self.update_redis_trusted_values(node_name, this_qubit,this_transmon_param,latex)
#
#
#class Multiplexed_DRAG_Derivative_Analysis(BaseAnalysis):
#    def __init__(self,result_dataset,node_name):
#        super().__init__(result_dataset)
#        qubit_labels = [ result_dataset[coord].long_name for coord in result_dataset.coords ]
#        qubits = sorted(set( qubit_labels )) #TODO there should be a better way
#        for indx, this_qubit in enumerate(qubits):
#            ds = _from_qubit_to_dataset(this_qubit, result_dataset)
#            motzois = ds.mw_motzoi_BATCHED.size
#            sums = [sum(ds.y0[:,this_motzoi_index].values) for this_motzoi_index in range(motzois)]
#            index_of_min = np.argmin(np.array(sums))
#            optimal_motzoi = float(ds.mw_motzoi_BATCHED[index_of_min].values)
#
#            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
#
#            ds.y0.plot(ax=this_axis)
#            this_axis.axvline(optimal_motzoi, c='red', lw=4)
#            self.qoi = optimal_motzoi
#            self.update_redis_trusted_values(node_name, this_qubit,'mw_motzoi','')
#            # this_axis.set_title(f'{node_name} for {this_qubit}')
#
#class Multiplexed_DRAG_Amplitude_Analysis(BaseAnalysis):
#    def __init__(self,result_dataset,node_name):
#        super().__init__(result_dataset)
#        qubit_labels = [ result_dataset[coord].long_name for coord in result_dataset.coords ]
#        qubits = sorted(set( qubit_labels )) #TODO there should be a better way
#        for indx, this_qubit in enumerate(qubits):
#            ds = _from_qubit_to_dataset(this_qubit, result_dataset)
#            amplitudes = ds.mw_amp180_BATCHED.size
#            sums = [sum(ds.y0[:,this_ampl_index].values) for this_ampl_index in range(amplitudes)]
#            index_of_max = np.argmax(np.array(sums))
#            optimal_amplitude = float(ds.mw_amp180_BATCHED[index_of_max].values)
#
#            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
#
#            ds.y0.plot(ax=this_axis)
#            this_axis.axvline(optimal_amplitude, c='red', lw=4)
#            self.qoi = optimal_amplitude
#            self.update_redis_trusted_values(node_name, this_qubit,'mw_amp180','')
#            # this_axis.set_title(f'{node_name} for {this_qubit}')
#
#class Multiplexed_Punchout_Analysis(BaseAnalysis):
#    def __init__(self,result_dataset,node_name):
#        super().__init__(result_dataset)
#        qubit_labels = [ result_dataset[coord].long_name for coord in result_dataset.coords ]
#        qubits = sorted(set( qubit_labels )) #TODO there should be a better way
#        for indx, this_qubit in enumerate(qubits):
#            ds = _from_qubit_to_dataset(this_qubit, result_dataset)
#            N_amplitudes = ds.dims['ro_ampl_BATCHED']
#            norm_factors = np.array([max(ds.y0[ampl].values) for ampl in range(N_amplitudes)])
#            ds['y0_norm'] = ds.y0 / norm_factors[:,None]
#
#            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
#
#            ds.y0_norm.plot(ax=this_axis)
#            # self.qoi = optimal_motzoi
#            # self.update_redis_trusted_values(node_name, this_qubit,'mw_motzoi','')
#            # this_axis.set_title(f'{node_name} for {this_qubit}')
#
#            handles, labels = this_axis.get_legend_handles_labels()
#            patch = mpatches.Patch(color='red', label=f'{this_qubit}')
#            handles.append(patch)
#            this_axis.set(title=None)
#            this_axis.legend(handles=handles)
#
#
#class Multiplexed_SSRO_simple_Analysis(BaseAnalysis):
#    def __init__(self,result_dataset,node_name):
#        super().__init__(result_dataset)
#        qubit_labels = [ result_dataset[coord].long_name for coord in result_dataset.coords ]
#        qubits = sorted(set( qubit_labels )) #TODO there should be a better way
#        for indx, this_qubit in enumerate(qubits):
#            ds = _from_qubit_to_dataset(this_qubit, result_dataset)
#            I = ds.y0.values
#            Q = ds.y1.values
#            rngs = ds.state_level.values.astype(int)
#            y = rngs
#            IQ = np.array([I, Q]).T
#            lda = LinearDiscriminantAnalysis(solver = "svd", store_covariance=True)
#
#            # run the discrimination, y_pred are the predicted levels
#            y_pred = lda.fit(IQ,y).predict(IQ)
#
#            tp = y == y_pred # True Positive
#            tp0 = tp[y == 0] # true positive levels when reading 0
#            tp1 = tp[y == 1] # true positive levels when reading 1
#            tp2 = tp[y == 2] # true positive levels when reading 2
#
#            IQ0 = IQ[y == 0] # IQ when reading 0
#            IQ1 = IQ[y == 1] # IQ when reading 1
#            IQ2 = IQ[y == 2] # IQ when reading 2
#
#            IQ0_tp = IQ0[ tp0] # True Positive when sending 0
#            IQ0_fp = IQ0[~tp0]
#            IQ1_tp = IQ1[ tp1] # True Positive when sending 1
#            IQ1_fp = IQ1[~tp1]
#            IQ2_tp = IQ2[ tp2] # True Positive when sending 2
#            IQ2_fp = IQ2[~tp2]
#
#            IQ0_positives = [IQ0_tp,IQ0_fp]
#            IQ1_positives = [IQ1_tp,IQ1_fp]
#            IQ2_positives = [IQ2_tp,IQ2_fp]
#
#            this_axis = self.axs[indx//self.column_grid, indx%self.column_grid]
#            SSRO_analysis.single_plotter(this_axis, lda, IQ0_positives, IQ1_positives, IQ2_positives)
#            # Save each discriminator
#            this_demo_qubit = int(this_qubit[1:]) % 16
#            if this_demo_qubit == 12: this_demo_qubit = 10
#            if this_demo_qubit == 14: this_demo_qubit = 11
#            joblib.dump(lda, f'q{this_demo_qubit}.set_classifier')
#
#            handles, labels = this_axis.get_legend_handles_labels()
#            patch = mpatches.Patch(color='red', label=f'{this_qubit}')
#            handles.append(patch)
#            this_axis.set(title=None)
#            this_axis.legend(handles=handles)
#
