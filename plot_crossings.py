import numpy as np
import matplotlib.pyplot as plt
import qutip as qp

N = 4
aq = qp.tensor(qp.destroy(N), qp.qeye(N))
ac = qp.tensor(qp.qeye(N), qp.destroy(N))


nq = aq.dag() * aq
nc = ac.dag() * ac

omega_q = 5.0 * 2 * np.pi
alpha_q = -0.2 * 2 * np.pi

fluxes = np.linspace(-0.3, 0.3, 200)
omega_c_max = 7 * 2 * np.pi
coupler_omegas = omega_c_max * np.sqrt(np.abs(np.cos(2 * np.pi * fluxes)))
# print(f"{ coupler_omegas / 2 / np.pi = }")
alpha_c = -0.2 * 2 * np.pi
g = 0.05 * 2 * np.pi

n_eigenstates = 6
energies = np.zeros((len(coupler_omegas), n_eigenstates))
omega_q_list = []
omega_c_list = []
model_fluxes = []

for index, omega_c in enumerate(coupler_omegas):
    H_q = omega_q * nq + (alpha_q / 2) * aq.dag() * aq.dag() * aq * aq
    H_c = omega_c * nc + (alpha_c / 2) * ac.dag() * ac.dag() * ac * ac

    Hint = g * (aq.dag() * ac + aq * ac.dag())

    H = H_q + H_c + Hint

    evals, states = H.eigenstates()

    for k in range(1, n_eigenstates):

        psi = states[k]
        q_expect = qp.expect(nq, psi)
        c_expect = qp.expect(nc, psi)
        if np.isclose(q_expect + c_expect, 1.0):
            if q_expect > 0.99:
                omega_q_list.append(evals[k])
                model_fluxes.append(fluxes[index])
            if c_expect > 0.95:
                omega_c_list.append(evals[k])


qubit_frequencies = np.abs(np.array(omega_q_list)) / 2 / np.pi
coupl_frequencies = np.abs(np.array(omega_c_list)) / 2 / np.pi

anal_freq_plus = (omega_q + coupler_omegas) / 2 + np.sqrt(
    ((omega_q - coupler_omegas) / 2) ** 2 + g**2
)
anal_freq_minus = (omega_q + coupler_omegas) / 2 - np.sqrt(
    ((omega_q - coupler_omegas) / 2) ** 2 + g**2
)
deltas = omega_q - coupler_omegas
thetas = np.arctan(2 * g / deltas) / 2
qubit_weights_plus = np.logical_and(np.cos(thetas) ** 2 > 0.99, deltas > 0)
qubit_weights_minus = np.logical_and(np.cos(thetas) ** 2 > 0.99, deltas < 0)

anal_freq_minus /= 2 * np.pi
anal_freq_plus /= 2 * np.pi
# print(f"{ anal_freq_minus = }")
# print(f"{ anal_freq_plus = }")
# print(f"{ qubit_weights = }")
anal_qubit_frequencies_plus = anal_freq_plus[qubit_weights_plus]
anal_qubit_frequencies_minus = anal_freq_minus[qubit_weights_minus]
anal_fluxes_plus = fluxes[qubit_weights_plus]
anal_fluxes_minus = fluxes[qubit_weights_minus]
# anal_coupl_frequencies = anal_freq_plus[~qubit_weights]
# anal_qubit_frequencies = anal_freq_minus[~qubit_weights]
# print(f"{ anal_qubit_frequencies = }")

# Plot
plt.figure(figsize=(8, 6))

# for j in range(n_eigenstates):
#     plt.plot(fluxes, energies[:, j] / (2 * np.pi), "b")

plt.plot(model_fluxes, qubit_frequencies, "bo")
plt.plot(anal_fluxes_plus, anal_qubit_frequencies_plus, "r-", lw=3)
plt.plot(anal_fluxes_minus, anal_qubit_frequencies_minus, "r-", lw=3)
# plt.plot(coupl_frequencies, "ro")
# plt.xlabel("Tunable oscillator frequency ω₂ / 2π")
# plt.ylabel("Energy levels / 2π")
# plt.title("Avoided crossings of two coupled anharmonic oscillators")

plt.grid()

plt.show()
