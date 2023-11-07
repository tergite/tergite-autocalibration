import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from analysis.qubit_spectroscopy_analysis import QubitSpectroscopyAnalysis
from analysis.coupler_spectroscopy_analysis import CouplerSpectroscopyAnalysis
from numpy.polynomial.polynomial import Polynomial
import math


ds = xr.open_dataset('coupler20231106/dataset.hdf5')
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
analysis = CouplerSpectroscopyAnalysis(ds)
fig, ax = plt.subplots()
# analysis = QubitSpectroscopyAnalysis(arr)
analysis.run_fitting()
currents, frequencies = zip(*analysis.qubit_frequencies)
currents = np.array(currents)
cutoff = 19
cut_currents = currents[:cutoff]
fit_currents = np.linspace(cut_currents[0], cut_currents[-1], 100)
print(f'{ frequencies = }')
cut_frequencies = frequencies[:cutoff]
coupler_fit, stats = Polynomial.fit(cut_currents, cut_frequencies, 2, full=True)
print( stats)
print(f'{ coupler_fit = }')
print( coupler_fit)
plt.plot( currents, np.array(frequencies) ,'ro-')
# plt.plot( fit_currents, coupler_fit(fit_currents),'r-')

def reject_outliers(data, m = 4):
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d/mdev if mdev else np.zeros(len(d))
    return np.array(s>m)


second_der = np.gradient(np.gradient(frequencies))
# distances = euklidian(currents, second_der)
distances = np.abs(np.gradient(frequencies))
print(f'{ distances = }')
array_splits =  reject_outliers(distances).nonzero()[0] + 1
print(f'{ array_splits = }')
frequency_splits = np.split(frequencies, array_splits)
currents_splits = np.split(currents, array_splits)
data = zip(currents_splits, frequency_splits)
roots = []
for split_currents, split_frequencies in data:
    if len(split_frequencies) > 4:
        # plt.plot(split_currents, split_frequencies, '-', lw=4)
        coupler_fit = Polynomial.fit(split_currents, split_frequencies, 4)
        fit_currents = np.linspace(split_currents[0], split_currents[-1], 100)
        plt.plot(fit_currents, coupler_fit(fit_currents), 'b-')
        root = np.mean(np.real(coupler_fit.roots()))
        roots.append(root)
        plt.plot( root, coupler_fit(root), 'kx', ms=12)

if len(roots) != 2:
    raise ValueError('Fit did not find two roots')

I0 = roots[np.argmin(np.abs(roots))]
I1 = roots[np.argmax(np.abs(roots))]
DeltaI = I1 - I0
possible_I = np.array([0.3 * DeltaI + I0, 0.3 * DeltaI - I0])
parking_I = possible_I[np.argmin(np.abs(possible_I))]
plt.axvline(parking_I, lw=3, c='red')
print(f'{ I0 = }')
print(f'{ parking_I = }')

# plt.plot( currents, np.gradient(frequencies) ,'go-')
# analysis.plotter(ax)
plt.show()
