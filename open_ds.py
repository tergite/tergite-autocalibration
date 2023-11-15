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


ds = xr.open_dataset('multidim20231115/20231115-132744-958-b74520-qubit_01_spectroscopy_multidim/dataset.hdf5')
# print(f'{ ds.yq21.attrs = }')
ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)

#---
for d_var in ds.data_vars:
    ds[d_var].attrs = {'qubit': d_var[1:4]}

#---
for qubit in qubits:
    fig, ax = plt.subplots()
    arr = 'y' + qubit
    dataset = ds[arr].to_dataset(promote_attrs = True)
    dataset[arr].values = np.abs(ds[arr].values)
# print(f'{ d16 = }')
    analysis = QubitSpectroscopyMultidim(dataset)
    analysis.run_fitting()
    analysis.plotter(ax)
    plt.show()

# data_var = list(ds.data_vars.keys())[0]

# ds[data_var].plot()

