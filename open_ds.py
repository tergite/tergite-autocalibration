import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from utilities.user_input import qubits
import importlib
import analysis.randomized_benchmarking_analysis as rnb
importlib.reload(rnb)


ds = xr.open_dataset('data_directory/20240206/20240206-171551-503-b05458-randomized_benchmarking/dataset.hdf5')
# print(f'{ ds.yq21.attrs = }')
ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
#---
rb = rnb.RandomizedBenchmarkingAnalysis(ds)
#---
complex_values = rb.S21.isel(
    {rb.seed_coord: [0]}
).values

complex_values = complex_values.flatten()
calib_0 = complex_values[-2]
calib_1 = complex_values[-1]
displacement_vector = calib_1 - calib_0
rotation_angle = np.angle(displacement_vector)
translated_to_zero_values = complex_values[:-2] - calib_0
rotated_values = translated_to_zero_values * np.exp(-1j * rotation_angle)

I_calib_0 = complex_values[-2].real
Q_calib_0 = complex_values[-2].imag
I_calib_1 = complex_values[-1].real
Q_calib_1 = complex_values[-1].imag
I_quad = complex_values[:-2].real
Q_quad = complex_values[:-2].imag

I_quad_translated = translated_to_zero_values.real
Q_quad_translated = translated_to_zero_values.imag

I_quad_rotated = rotated_values.real
Q_quad_rotated = rotated_values.imag

plt.plot( I_quad, Q_quad,'bo-')
plt.plot( I_calib_0, Q_calib_0,'ko')
plt.plot( I_calib_1, Q_calib_1,'ro')

plt.plot( I_quad_translated, Q_quad_translated,'go-')
plt.plot( I_quad_rotated, Q_quad_rotated,'mo-')

plt.axvline(0)
plt.axhline(0)
plt.show()
#---

plt.plot( rb.I_quad, rb.Q_quad,'bo-')
plt.show()

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

