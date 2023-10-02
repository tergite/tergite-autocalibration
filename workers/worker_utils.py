import xarray

def configure_dataset(
        raw_ds: xarray.Dataset,
        samplespace: dict[str, dict[str,np.ndarray]],
        ) -> xarray.Dataset:
    '''The dataset retrieved from the instrument coordinator  is
       too bare-bones. Here we configure the dims, coords and data_vars'''

    dataset = xarray.Dataset()

    keys = raw_ds.data_vars.keys()
    sweep_quantities = samplespace.keys() # for example 'ro_frequencies', 'ro_amplitudes' ,...
    sweep_parameters = list(samplespace.values())[0]
    qubits = list(sweep_parameters.keys())
    n_qubits = len(qubits)
    if 'ro_opt_frequencies' in list(sweep_quantities):
        qubit_states = [0,1,2]

    for key in keys:
        key_indx = key%n_qubits # this is to handle ro_opt_frequencies node where
        # there are 2 or 3 measurements (i.e 2 or 3 Datarrays) for each qubit
        coords_dict = {}
        qubit = qubits[key_indx]
        for quantity in sweep_quantities :
            coord_key = quantity+qubit
            settable_values = samplespace[quantity][qubit]
            coord_attrs = {'qubit':qubit, 'long_name': f'{coord_key}', 'units': 'NA'}
            #coords_dict[coord_key] = (quantity, settable_values, coord_attrs)
            coords_dict[coord_key] = (coord_key, settable_values, coord_attrs)
        partial_ds = xarray.Dataset(coords=coords_dict)
        dimensions = [len(samplespace[quantity][qubit]) for quantity in sweep_quantities]
        # TODO this is not safe:
        # This assumes that the inner settable variable is placed
        # at the first position in the samplespace

        reshaping = reversed(dimensions)
        data_values = raw_ds[key].values.reshape(*reshaping)
        data_values = np.transpose(data_values)
        attributes = {'qubit': qubit, 'long_name': f'y{qubit}', 'units': 'NA'}
        qubit_state = ''
        if 'ro_opt_frequencies' in list(sweep_quantities):
            qubit_state = qubit_states[key // n_qubits]
            attributes['qubit_state'] = qubit_state
        #breakpoint()
        #real_data_array = xarray.DataArray(
        #                     data=data_values.real, 
        #                     coords=coords_dict,
        #                     dims='ro_frequencies',
        #                     attrs=attributes
        #                )
        #partial_ds[f'y{qubit}_real{qubit_state}'] = real_data_array

        partial_ds[f'y{qubit}_{qubit_state}'] = (tuple(coords_dict.keys()), data_values, attributes)
        dataset = xarray.merge([dataset,partial_ds])
    return dataset

def to_real_dataset(iq_dataset: xarray.Dataset) -> xarray.Dataset:
    dataset_dict = {}
    real_ds = xarray.Dataset(coords=iq_dataset.coords)
    for var in iq_dataset.data_vars.keys():
        this_qubit = iq_dataset[var].attrs['qubit']
        attributes = {'qubit': this_qubit}
        this_state = ''
        if 'qubit_state' in iq_dataset[var].attrs:
            qubit_state = iq_dataset[var].attrs["qubit_state"]
            this_state = qubit_state
            attributes['qubit_state'] = qubit_state

        qubit_coords = iq_dataset[f'y{this_qubit}_{this_state}'].coords
        values = iq_dataset[var].values
        qubit_key = f'y{this_qubit}_{this_state}'
        real_ds[qubit_key+'_real'] = (qubit_coords, values.real, attributes)
        real_ds[qubit_key+'_imag'] = (qubit_coords, values.imag, attributes)

    return real_ds

def handle_ro_freq_optimization(complex_dataset: xarray.Dataset, states: list[int]) -> xarray.Dataset:
    new_ds = xarray.Dataset(coords=complex_dataset.coords, attrs=complex_dataset.attrs)
    new_ds = new_ds.expand_dims(dim={'qubit_state': states})
    #TODO this for every var and every coord. It might cause
    # performance issues for larger datasets
    for coord in complex_dataset.coords:
        this_qubit = complex_dataset[coord].attrs['qubit']
        attributes = {'qubit': this_qubit}
        values = []
        for var in complex_dataset.data_vars:
            if coord in complex_dataset[var].coords:
                values.append(complex_dataset[var].values)
        new_ds[f'y{this_qubit}'] = (('qubit_state',coord), np.vstack(values), attributes)

    return new_ds
    # xarray.concat([result_dataset_complex.yq160, result_dataset_complex.yq161],'ro_opt_frequenciesq16', combine_attrs='drop_conflicts')
