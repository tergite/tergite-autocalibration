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
    return omega_max * np.abs(np.cos(np.pi * phi_ratio))

phi_ratios = np.linspace(-1, 1, 400)

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
data_ge = np.array(g_to_e_frequencies) + np.random.random(len(g_to_e_frequencies)) * 5e6
data_gf = np.array(g_to_f_frequencies) + np.random.random(len(g_to_f_frequencies)) * 5e6
data_combined = np.array(combined_frequencies) + np.random.random(len(combined_frequencies)) * 5e6

#---
plt.plot(g_to_e_phi_ratios, data_ge, 'bo-')
plt.plot(g_to_f_phi_ratios, data_gf, 'go-')
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
peaks, properties = signal.find_peaks(np.abs(gradient_combined), prominence=20e6, width=2)
# plt.plot(combined_phi_ratios, np.abs(gradient_combined), 'ro-')
# plt.plot(np.array(combined_phi_ratios)[peaks], np.abs(gradient_combined)[peaks], 'x', ms=20)
# plt.show()
print(f'{ peaks = }')

def pairwise(iterable):
    #TODO after python 3.10 this will be replaced by itertools.pairwise
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    iterable = [0] + list(iterable) + [len(data_combined)]
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

slicing = list(pairwise(peaks))
for slice_ in slicing:
    this_slice = slice(*slice_)
    diff = np.mean(data_combined) - np.mean(data_combined[this_slice])
    print(diff)

## change the coupler maximum value for guess

def coupler_model(omega_max, omega2, g12):
    pass

import lmfit
class CouplerModel(lmfit.model.Model):
    """
    Model for data which follows a coupler function.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(coupler_model, *args, **kwargs)

        self.set_param_hint("wmax", vary=True)
        self.set_param_hint("w2", vary=True)
        self.set_param_hint("g12", vary=True)
        self.set_param_hint("m", vary=True)
        self.set_param_hint("phi_off", vary=True)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters | None:
        x = kws.get("x", None)

        if x is None:
            return None

        # Guess coupler max frequency value
        omega_max_guess = 6e9* 2 * np.pi
        self.set_param_hint("omega_max", value=omega_max_guess)

        # Guess qubit 2 frequency value
        omega2_guess = freq_flat_one* 2 * np.pi  # the value near gradient zero
        self.set_param_hint("omega2", value=omega2_guess)

        # #guess m_value
        # bias_max=np.max(DCbias)
        # bias_min=np.min(DCbias)
        # size_bias=bias_max-bias_min
        #
        # m_guess = size_bias*2/num_avoided_cross
        # self.set_param_hint("m", value=m_guess)

        # Guess phi_offset
        #normally phase offset is not large
        # phi_off_guess = 0
        # self.set_param_hint("phi_off", value=phi_off_guess)

        ## guessing g12
        # pair_obj=closest_array_items(arr1, arr2) #arr1 is higher minima arr2 is lower minima
        # #scaling to phi
        # angle1=(1/phi_0)*((phi_0/m_guess)*(pair_obj[0]-phi_off_guess))
        # angle2=(1/phi_0)*((phi_0/m_guess)*(pair_obj[1]-phi_off_guess))
        # obj1=(wmax_guess/2/pi)*abs(np.cos(angle1))
        # obj2=(wmax_guess/2/pi)*abs(np.cos(angle2))
        #
        # eDistance = math.dist([obj1, freq_flat_one], [obj2, freq_flat_two])
        #print(eDistance)

        # g12_guess=(eDistance/2)* 2 * pi
        # self.set_param_hint("g12", value=g12_guess)
        #self.set_param_hint("g12", value=100e6*2 * pi, min=60e6*2 * pi, max=120e6*2 * pi)


        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)
