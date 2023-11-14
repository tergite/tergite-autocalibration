import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from analysis.qubit_spectroscopy_analysis import QubitSpectroscopyAnalysis
from analysis.qubit_spectroscopy_multidim import QubitSpectroscopyMultidim
from analysis.coupler_spectroscopy_analysis import CouplerSpectroscopyAnalysis
from numpy.polynomial.polynomial import Polynomial
from nodes.node import NodeFactory
from workers.post_processing_worker import post_process


ds = xr.open_dataset('coupler20231113/dataset.hdf5')
# print(f'{ ds.yq21.attrs = }')
ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)

#---
for data_var in ds.data_vars:
    ds[data_var].attrs = {'qubit': data_var[1:4]}

#---
fig, ax = plt.subplots()
#---
d16 = ds.yq16.to_dataset(promote_attrs = True)
d16.yq16.values = np.abs(ds.yq16.values)
# print(f'{ d16 = }')
analysis = QubitSpectroscopyMultidim(d16)
analysis.run_fitting()
analysis.plotter(ax)
plt.show()

# data_var = list(ds.data_vars.keys())[0]

# ds[data_var].plot()

