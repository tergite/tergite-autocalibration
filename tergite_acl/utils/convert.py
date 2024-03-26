# This is a temporary fix to standardize parameter and
# properties/attributes of transmon's component e.g.
# qubit, readout resonator, couplers etc.
# The standardization is necessary as the redis storage
# differs in calibration on qblox instrument using
# quantify and standard redis storage in bcc.
# this file can be discarded when no mapping would be
# necessary.

import warnings
from typing import List, Any

import redis

import tergite_acl.utils.storage as store
from tergite_acl.utils.logger.bcc_logger import get_logger
from tergite_acl.config.settings import REDIS_CONNECTION

logger = get_logger()

param_map = {
    "clock_freqs:readout": ("readout_resonator", "frequency", "Hz", float),

    # probably this is not needed ->
    "measure:pulse_ampl": ("readout_resonator", "pulse_amplitude", "Hz", float),

    "extended_clock_freqs:readout_2state_opt": ("readout_resonator", "frequency_opt", "Hz", float),

    "measure:pulse_amp": ("readout_resonator", "pulse_amplitude", "V", float),
    "measure_1:ro_freq_1": ("readout_resonator", "frequency_1", "Hz", float),
    "measure_2:ro_freq_2": ("readout_resonator", "frequency_2", "Hz", float),
    "measure_2state_opt:ro_ampl_2st_opt": ("readout_resonator", "pulse_amplitude", "V", float),
    "measure:pulse_duration": ("readout_resonator", "pulse_duration", "Sec", float),
    "measure:_type": ("readout_resonator", "pulse_type", "None", str),

    # probably this should be deprecated ->
    "measure:ro_pulse_delay": ("readout_resonator", "pulse_delay", "Sec", float),

    "measure:acq_delay": ("readout_resonator", "acq_delay", "Sec", float),
    "measure:integration_time": ("readout_resonator", "acq_integration_time", "Sec", float),
    "clock_freqs:f01": ("qubit", "frequency", "Hz", float),
    "rxy:amp180": ("qubit", "pi_pulse_amplitude", "V", float),
    "rxy:duration": ("qubit", "pi_pulse_duration", "Sec", float),
    "rxy:sigma": ("qubit", "pulse_sigma", "None", float),
    "rxy:mw_pulse_type": ("qubit", "pulse_type", "None", float),
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
}

manual_param_map = {
    'rxy:mw_pulse_type': 'Gaussian',
    'measure:_type': 'Square',
    'measure:ro_pulse_delay': 4e-9,
    'rxy:duration': 5.2e-8,
    'rxy:sigma': 6.5e-9,
    't1_time': 0
}


def manual_checks(parameter_name_: str,
                  parameter_value_: Any,
                  overwrite_default: bool = False) -> Any:
    parsed_parameter_value_ = parameter_value_
    parameter_settings_ = param_map[parameter_name_]

    try:
        parsed_parameter_value_ = parameter_settings_[3](parsed_parameter_value_)
    except:
        if parameter_settings_[3] is not None:
            logger.warning(
                f'Cannot parse {parameter_value_} for {parameter_name_} to {parameter_settings_[3].__name__}')

    if parsed_parameter_value_ == 'nan':
        parsed_parameter_value_ = None

    if overwrite_default and parameter_name_ in manual_param_map.keys():
        parsed_parameter_value_ = manual_param_map[parameter_name_]

    return parsed_parameter_value_


def structured_redis_storage(field_key: str, comp_index: str, field_value, **kwarg):
    if field_key in param_map:
        parsed_value = manual_checks(field_key, field_value, overwrite_default=False)
        store.set_component_property(
            param_map[field_key][0],
            param_map[field_key][1],
            comp_index,
            value=parsed_value,
            unit=param_map[field_key][2],
            **kwarg
        )
    else:
        warnings.warn(
            f"'{field_key}' is not in mapped parameter list in utilities/standard_redis_storage.py. Please add appropriate parameter atributes in the map"
        )


def convert_all_redis_values(component_ids: List[str] = None):
    """
    This function will go through all redis values in the param_map and store them again in the structured format

    Args:
        component_ids: list of qubit names to take parameters from redis (parameter not implemented)

    """
    # TODO: The option with the qubits is currently not implemented, qubits and couplers are found automatically

    # We are reading the redis keys with the 'cs:' prefix
    # They contain information about whether a node is calibrated or not
    # Note: If the redis datastructure changes in the auto-calibration, we would have to adjust here
    components: List[str] = list(map(lambda x_: x_.strip('cs:'), REDIS_CONNECTION.keys('cs:*')))

    # We can identify the couplers, because they are in the format e.g. q12_q13
    couplers = list(filter(lambda x_: '_' in x_, components))
    # Remaining components are the qubits e.g. q12, q13, q14
    qubits = sorted(list(set(components).difference(set(couplers))))

    # TODO: Implement some checks, whether all calibration nodes are done

    def read_redis_value_calibration_format(component_prefix: str,
                                            component_id: str,
                                            parameter_key: str):
        # TODO: add some error handling
        value_ = REDIS_CONNECTION.hget(f'{component_prefix}:{component_id}', parameter_key)
        return value_

    # We iterate over all qubits to read and convert their parameter values inside the redis storage
    for qubit in qubits:
        for parameter_name in param_map.keys():
            parameter_value = read_redis_value_calibration_format('transmons',
                                                                  qubit,
                                                                  parameter_name)
            parameter_value = manual_checks(parameter_name, parameter_value, overwrite_default=True)
            if parameter_value is not None:
                structured_redis_storage(parameter_name, qubit.strip('q'), parameter_value)

        # TODO: Implement the update of the discriminator as it is stored elsewhere
        # Iterate over lda_parameter and lda_coeff

    # TODO: Implement the same procedure for couplers
    # Currently there is no standardized format for couplers in the mongoDB
