# This code is part of Tergite
#
# (C) Copyright Abdullah-Al Amin 2023
# (C) Copyright Stefan Hill 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# This is a temporary fix to standardize parameter and
# properties/attributes of transmon's component e.g.
# qubit, readout resonator, couplers etc.
# The standardization is necessary as the redis storage
# differs in calibration on qblox instrument using
# quantify and standard redis storage in bcc.
# this file can be discarded when no mapping would be
# necessary.

# Keeping this for reference until merge request is closed

param_map = {
    "clock_freqs:readout": ("readout_resonator", "frequency", "Hz", float),
    # probably this is not needed ->
    "measure:pulse_ampl": ("readout_resonator", "pulse_amplitude", "Hz", float),
    "extended_clock_freqs:readout_2state_opt": (
        "readout_resonator",
        "frequency_opt",
        "Hz",
        float,
    ),
    "measure:pulse_amp": ("readout_resonator", "pulse_amplitude", "V", float),
    "measure_1:ro_freq_1": ("readout_resonator", "frequency_1", "Hz", float),
    "measure_2:ro_freq_2": ("readout_resonator", "frequency_2", "Hz", float),
    "measure_2state_opt:ro_ampl_2st_opt": (
        "readout_resonator",
        "pulse_amplitude",
        "V",
        float,
    ),
    "measure:pulse_duration": ("readout_resonator", "pulse_duration", "Sec", float),
    "measure:_type": ("readout_resonator", "pulse_type", "None", str),
    # probably this should be deprecated ->
    "measure:ro_pulse_delay": ("readout_resonator", "pulse_delay", "Sec", float),
    "measure:acq_delay": ("readout_resonator", "acq_delay", "Sec", float),
    "measure:integration_time": (
        "readout_resonator",
        "acq_integration_time",
        "Sec",
        float,
    ),
    "clock_freqs:f01": ("qubit", "frequency", "Hz", float),
    "rxy:amp180": ("qubit", "pi_pulse_amplitude", "V", float),
    "rxy:duration": ("qubit", "pi_pulse_duration", "Sec", float),
    "rxy:sigma": ("qubit", "pulse_sigma", "None", float),
    "rxy:mw_pulse_type": ("qubit", "pulse_type", "None", str),
    "rxy:motzoi": ("qubit", "motzoi_parameter", "V", float),
    "t1_time": ("qubit", "t1_decoherence", "Sec", float),
    "clock_freqs:f12": ("qubit", "frequency_12", "Hz", float),
    "r12:ef_amp180": ("qubit", "pi_pulse_ef_amplitude", "V", float),
    # We are currently using the linear discriminator
    "lda_coef_0": ("discriminator", "coef_0", None, float),
    "lda_coef_1": ("discriminator", "coef_1", None, float),
    "lda_intercept": ("discriminator", "intercept", None, float),
    # TODO: This is the new way of doing discrimination, we would have to update TQC and the BCC postprocessing though
    "measure_2state_opt:acq_rotation": ("discriminator", "rotation", "V", float),
    "measure_2state_opt:acq_threshold": ("discriminator", "threshold", "V", float),
    # characterization
    "selectivity": ("qubit", "XY_crosstalk", None, None),
    "anharmonicity": ("qubit", "anharmonicity", None, None),
    "fidelity": ("qubit", "fidelity", None, None),
    "purity_fidelity": ("qubit", "purity_fidelity", None, None),
}

manual_param_map = {
    "rxy:mw_pulse_type": "Gaussian",
    "measure:_type": "Square",
    "measure:ro_pulse_delay": 4e-9,
    "rxy:duration": 5.2e-8,
    "rxy:sigma": 6.5e-9,
    "t1_time": 0,
}
