from itertools import tee
import numpy as np
import matplotlib.pyplot as plt
import qutip as qt
from qutip.qobj import Qobj
from scipy import signal

sz1 = qt.tensor(qt.sigmaz(), qt.qeye(2))
sx1 = qt.tensor(qt.sigmax(), qt.qeye(2))

sz2 = qt.tensor(qt.qeye(2), qt.sigmaz())
sx2 = qt.tensor(qt.qeye(2), qt.sigmax())

def hamiltonian(omega1, omega2, g12) -> Qobj:
    return 1/2 * omega1 * sz1 + 1/2 * omega2 * sz2 + g12 * sx1 * sx2

omega_max = 2 * np.pi * 8.49e9

def omega_tunable(phi_ratio):
    # phi_ratio = phi / phi_0
    return omega_max * np.abs(np.cos(np.pi * (phi_ratio - 0.2)))

phi_ratios = np.linspace(-1, 1, 60)

def eigenvalues(omega1):
    g12 = 95e6 * 2 * np.pi
    omega2 = 4.0e9 * 2 * np.pi
    h = hamiltonian(omega1, omega2, g12)
    evals, ekets = h.eigenstates()
    return evals

#---
g_to_e = []
g_to_f = []
combined_data = []
f_min = 3.90e9
f_max = 4.10e9
for phi_ratio in phi_ratios:
    omega = omega_tunable(phi_ratio)
    evals = eigenvalues(omega)
    f_ge = (evals[1] - evals[0]) / 2 / np.pi  # frequncy from ground to 1st excited
    if  f_min < f_ge < f_max:
        g_to_e.append((phi_ratio, f_ge))
        combined_data.append((phi_ratio, f_ge))
    f_gf = (evals[2] - evals[0]) / 2 / np.pi  # frequncy from ground to 2nd excited
    if  f_min < f_gf < f_max:
        g_to_f.append((phi_ratio, f_gf))
        combined_data.append((phi_ratio, f_gf))

g_to_e_phi_ratios, g_to_e_frequencies = list(zip(*g_to_e))
g_to_f_phi_ratios, g_to_f_frequencies = list(zip(*g_to_f))
combined_phi_ratios, combined_frequencies = list(zip(*combined_data))

#---
plt.plot(g_to_e_phi_ratios, g_to_e_frequencies, 'bo-')
plt.plot(g_to_f_phi_ratios, g_to_f_frequencies, 'go-')
plt.show()

#---
from numpy.polynomial.polynomial import Polynomial
def pairwise(iterable):
    #TODO after python 3.10 this will be replaced by itertools.pairwise
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    iterable = [0] + list(iterable) + [len(data_combined)]
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

data_ge = np.array(g_to_e_frequencies) + np.random.random(len(g_to_e_frequencies)) * 5e6
data_gf = np.array(g_to_f_frequencies) + np.random.random(len(g_to_f_frequencies)) * 5e6
data_combined = np.array(combined_frequencies) + np.random.random(len(combined_frequencies)) * 5e6

diffs = np.abs(np.diff(data_combined))
min_diff_index = np.argmin(diffs)
# plt.plot( np.abs(diffs),'bo-')
peaks, properties = signal.find_peaks(diffs, prominence= 10e6, width=0)
# plt.plot(
#     np.array(range(len(diffs)))[peaks], np.abs(diffs)[peaks],'rx'
# )
# plt.plot(combined_phi_ratios, data_combined,'bo-')
plt.axvline(np.array(combined_phi_ratios)[min_diff_index], lw=2, c='green')
for peak in peaks:
    plt.axvline(np.array(combined_phi_ratios)[peak], lw=2, c='red')
# plt.show()
d1 = np.array(combined_phi_ratios)[2] - np.array(combined_phi_ratios)[0]
d2 = np.array(combined_phi_ratios)[3] - np.array(combined_phi_ratios)[1]
above = np.array([])
below = np.array([])
phis_above = np.array([])
phis_below = np.array([])
slicing = list(pairwise(peaks))
plt.show()
for slice_ in slicing:
    for peak in peaks:
        plt.axvline(np.array(combined_phi_ratios)[peak], lw=2, c='red')
    this_slice = slice(*slice_)
    phis = np.array(combined_phi_ratios[this_slice])
    phis_space = np.linspace(phis[0], phis[-1], 100)
    data = np.array(data_combined[this_slice])
    poly_fit = Polynomial.fit(phis, data, 2)
    print( poly_fit)
    print(f'{ poly_fit = }')
    print(poly_fit(np.array([0,0.2])))
    print( )
    plt.plot( phis_space, poly_fit(phis_space),'bo-')
    plt.plot( phis, data, 'ro')
    plt.show()

    # diff = np.mean(data_combined) - np.mean(data_combined[this_slice])
    # if diff < 0 :
    #     below = np.concatenate((below, data_combined[this_slice]))
    #     phis_below = np.concatenate((phis_below, combined_phi_ratios[this_slice]))
    # else:
    #     above = np.concatenate((above, data_combined[this_slice]))
    #     phis_above = np.concatenate((phis_above, combined_phi_ratios[this_slice]))
#---
from scipy.interpolate import splrep,splprep, splev, BSpline
from scipy.signal import find_peaks_cwt
from scipy import signal
tck = splrep(combined_phi_ratios, data_combined / 1e9,s=0)
tck50 = splrep(combined_phi_ratios, data_combined / 1e9,s=0., quiet=0)
fit_ratios = np.linspace(combined_phi_ratios[0], combined_phi_ratios[-1],200)
yder = splev(fit_ratios, tck50, der=1)

win = signal.windows.boxcar(5)
# winb = signal.windows.boxcar(20)
filtered = signal.convolve(np.abs(yder), win, mode='same') / np.sum(win)
# filteredb = signal.convolve(np.abs(yder), winb, mode='same') / np.sum(win)
# plt.plot(g_to_e_phi_ratios, data_ge, 'bo')
# plt.plot(g_to_f_phi_ratios, data_gf, 'go')
# plt.plot(combined_phi_ratios, data_combined / 1e9, 'go')
# plt.plot(fit_ratios, BSpline(*tck)(fit_ratios), '-')
# plt.plot(fit_ratios, BSpline(*tck50)(fit_ratios), '.')
plt.plot(fit_ratios, np.abs(yder), 'r-')
plt.plot(fit_ratios, filtered, 'g-')
# plt.plot(fit_ratios, filteredb, 'b-')
# plt.plot(fit_ratios[peaks2], np.abs(yder)[peaks2], 'x')
plt.show()

#---
gradient_ge = np.gradient(data_ge)
gradient_gf = np.gradient(data_gf)
gradient_combined = np.gradient(data_combined)
second_gradient_combined = np.gradient(gradient_combined)
# plt.plot(g_to_f_phi_ratios, gradient_gf, 'r.-')
# plt.plot(g_to_e_phi_ratios, gradient_ge, 'g.-')
plt.plot(combined_phi_ratios, np.abs(gradient_combined), 'ro-')
# plt.plot(combined_phi_ratios, second_gradient_combined, 'go-')
# plt.plot(g_to_e_phi_ratios, data_ge, 'ro-')
plt.show()

#---

peaks, properties = signal.find_peaks(np.abs(gradient_combined), prominence=2e6, width=1)
plt.plot(combined_phi_ratios, np.abs(gradient_combined), 'ro-')
plt.plot(np.array(combined_phi_ratios)[peaks], np.abs(gradient_combined)[peaks], 'x', ms=20)
plt.show()
# print(f'{ peaks = }')

def pairwise(iterable):
    #TODO after python 3.10 this will be replaced by itertools.pairwise
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    iterable = [0] + list(iterable) + [len(data_combined)]
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

above = np.array([])
below = np.array([])
phis_above = np.array([])
phis_below = np.array([])
slicing = list(pairwise(peaks))
for slice_ in slicing:
    this_slice = slice(*slice_)
    diff = np.mean(data_combined) - np.mean(data_combined[this_slice])
    if diff < 0 :
        below = np.concatenate((below, data_combined[this_slice]))
        phis_below = np.concatenate((phis_below, combined_phi_ratios[this_slice]))
    else:
        above = np.concatenate((above, data_combined[this_slice]))
        phis_above = np.concatenate((phis_above, combined_phi_ratios[this_slice]))

# plt.plot( phis_below, below,'bo')
# plt.plot( phis_above, above,'ro')
# plt.show()
#---

##################################################
# lmfit model
##################################################
def coupler_model(phi_ratios, omega_max, omega2, g12):
    def omega_tunable(phi_ratios):
        # phi_ratio is defined as phi / phi_0
        return omega_max * np.abs(np.cos(np.pi * phi_ratios))
    def eigenvalues(omega1):
        h = hamiltonian(omega1, omega2, g12)
        evals, _ = h.eigenstates()
        return evals
    omegas = omega_tunable(phi_ratios)
    frequencies = []
    for omega in omegas:
        evals = eigenvalues(omega)

        f_ge = (evals[1] - evals[0]) / 2 / np.pi  # frequncy from ground to 1st excited
        if f_min < f_ge < f_max:
            frequencies.append(f_ge)
        else:
            frequencies.append(3.91e9)
    return np.array(frequencies)


import lmfit
import datetime
class CouplerModel(lmfit.model.Model):
    """
    Model for data which follows a coupler function.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(coupler_model, *args, **kwargs)

        self.set_param_hint("omega_max", vary=True)
        self.set_param_hint("omega2", vary=True)
        self.set_param_hint("g12", vary=True)
        # self.set_param_hint("m", vary=True)

        # self.set_param_hint("phi_off", vary=True)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        phi_ratios = kws.get("phi_ratios", None)

        if phi_ratios is None:
            return None

        omega_max_guess = 8.49e9* 2 * np.pi
        self.set_param_hint("omega_max", value=omega_max_guess, min=0)

        # Guess qubit 2 frequency value
        omega2_guess = 4e9 * 2 * np.pi  # the value near gradient zero
        # omega2_guess = freq_flat_one* 2 * np.pi  # the value near gradient zero
        self.set_param_hint("omega2", value=omega2_guess, min=0)

        self.set_param_hint(
            "g12", value= 95e6 * 2 * np.pi, min=60e6 * 2 * np.pi, max=120e6 * 2 * np.pi
        )


        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)

model = CouplerModel()
# g_to_e_phi_ratios = np.array(g_to_e_phi_ratios)
guess = model.guess(data_ge, phi_ratios=g_to_e_phi_ratios)

# import cProfile
# cProfile.run('fit_result = model.fit(data_ge, params=guess, phi_ratios=g_to_e_phi_ratios)')
#---
start = datetime.datetime.now()
fit_result = model.fit(data_ge, params=guess, phi_ratios=g_to_e_phi_ratios)
finish = datetime.datetime.now()
print(f'{ finish - start = }')
#---
print(f'{ fit_result = }')
fit_ratios = np.linspace(g_to_e_phi_ratios[0], g_to_e_phi_ratios[-1],400)
fit_freqs = model.eval(fit_result.params, **{model.independent_vars[0]: fit_ratios})
#---
plt.plot(g_to_e_phi_ratios, data_ge, 'bo-')
plt.plot(fit_ratios, fit_freqs, 'r-')
plt.show()
