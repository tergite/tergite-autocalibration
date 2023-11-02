import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from analysis.qubit_spectroscopy_analysis import QubitSpectroscopyAnalysis
from analysis.coupler_spectroscopy_analysis import CouplerSpectroscopyAnalysis


ds = xr.open_dataset('coupler20231026/dataset.hdf5')
ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)

ds.yq21.values = np.abs(ds.yq21.values)
#---
# for i in range(20, 21):
#     ds.yq21[i].plot()
# plt.show()
#---
arr = ds.yq21[41]

arr.attrs = {'qubit': 'q00'}
arr = arr.to_dataset()


#---
ds.yq21.attrs = {'qubit': 'q21'}
print(f'{ ds = }')
# analysis = CouplerSpectroscopyAnalysis(ds)
fig, ax = plt.subplots()
analysis = QubitSpectroscopyAnalysis(arr)
analysis.run_fitting()
analysis.plotter(ax)
plt.show()
