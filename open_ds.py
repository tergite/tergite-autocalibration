import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from analysis.qubit_spectroscopy_analysis import QubitSpectroscopyAnalysis
from analysis.qubit_spectroscopy_multidim import QubitSpectroscopyMultidim
from analysis.coupler_spectroscopy_analysis import CouplerSpectroscopyAnalysis
from numpy.polynomial.polynomial import Polynomial
from nodes.node import NodeFactory
from workers.post_processing_worker import post_process
from utilities.user_input import qubits
import importlib
import analysis.cz_chevron_analysis
importlib.reload(analysis.cz_chevron_analysis)

analysis_class = analysis.cz_chevron_analysis.CZChevronAnalysis

ds = xr.open_dataset('data_directory/20231204/20231204-160058-215-c1cdcc-cz_chevron/dataset.hdf5')
# print(f'{ ds.yq21.attrs = }')
ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)

#---
for d_var in ds.data_vars:
    ds[d_var].attrs = {'qubit': d_var[1:4]}

#---
qubits = ['q21', 'q22']
for qubit in qubits:
    fig, ax = plt.subplots()
    arr = 'y' + qubit
    dataset = ds[arr].to_dataset(promote_attrs = True)
    dataset[arr].values = np.abs(ds[arr].values)
# print(f'{ d16 = }')
    analysis = analysis_class(dataset)
    analysis.run_fitting()
    analysis.plotter(ax)
    ax.legend()
    plt.show()

# data_var = list(ds.data_vars.keys())[0]

# ds[data_var].plot()

