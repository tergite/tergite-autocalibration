# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs AB 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from enum import Enum
from pathlib import Path
from typing import Tuple, Dict, Any, List, Type, Union

import tomlkit

from tergite_autocalibration.config.globals import REDIS_CONNECTION


class _DataSource(Enum):
    REDIS = "REDIS"
    LITERAL = "LITERAL"


def _deep_update(original_map_, update_map_):
    """
    Recursive function to deep update a dict. Function is commutative.

    Args:
        original_map_: Original dict with entries
        update_map_: Dict to update the entries

    Returns:

    """
    for key, value in update_map_.items():
        if (
            isinstance(value, dict)
            and key in original_map_
            and isinstance(original_map_[key], dict)
        ):
            _deep_update(original_map_[key], value)
        else:
            original_map_[key] = value
    return original_map_


_qubit_parameters = [
    ("frequency", "clock_freqs:f01", _DataSource.REDIS, float),
    ("pi_pulse_amplitude", "rxy:amp180", _DataSource.REDIS, float),
    ("pi_pulse_duration", "rxy:duration", _DataSource.REDIS, float),
    ("pulse_type", "Gaussian", _DataSource.LITERAL, str),
    ("pulse_sigma", "rxy:sigma", _DataSource.REDIS, float),
    ("t1_decoherence", "t1_time", _DataSource.REDIS, float),
    ("t2_decoherence", "t2_time", _DataSource.REDIS, float),
]

_readout_resonator_parameters = [
    ("acq_delay", "measure:acq_delay", _DataSource.REDIS, float),
    ("acq_integration_time", "measure:integration_time", _DataSource.REDIS, float),
    ("frequency", "clock_freqs:readout", _DataSource.REDIS, float),
    ("pulse_delay", "measure:ro_pulse_delay", _DataSource.REDIS, float),
    ("pulse_duration", "measure:pulse_duration", _DataSource.REDIS, float),
    ("pulse_type", "Square", _DataSource.LITERAL, str),
    ("pulse_amplitude", "measure_2state_opt:pulse_amp", _DataSource.REDIS, float),
]

_lda_parameters = [
    ("coef_0", "lda_coef_0", _DataSource.REDIS, float),
    ("coef_1", "lda_coef_1", _DataSource.REDIS, float),
    ("intercept", "lda_intercept", _DataSource.REDIS, float),
]

_coupler_parameters = [
    ("frequency", "cz_pulse_frequency", _DataSource.REDIS, float),
    ("cz_pulse_amplitude", "cz_pulse_amplitude", _DataSource.REDIS, float),
    ("cz_pulse_dc_bias", "parking_current", _DataSource.REDIS, float),
    ("cz_pulse_duration_constant", "cz_pulse_duration", _DataSource.REDIS, float),
    ("control_rz_lambda", "cz_dynamic_control", _DataSource.REDIS, float),
    ("target_rz_lambda", "cz_dynamic_target", _DataSource.REDIS, float),
    ("pulse_type", "wacqt_cz", _DataSource.LITERAL, str),
]


def _assemble_parameters(
    parameter_map: List[Tuple[str, str, "_DataSource", Type]],
    object_id: str,
    set_id: bool = True,
    redis_prefix: str = "transmons",
) -> Dict[str, Any]:

    # Add object id if necessary
    if not set_id:
        parameterized_return_object = {}
    else:
        parameterized_return_object = {"id": object_id}

    for parameter_ in parameter_map:
        if parameter_[2] == _DataSource.REDIS:
            redis_value_ = REDIS_CONNECTION.hget(
                f"{redis_prefix}:{object_id}", parameter_[1]
            )
            # parameter[3] is the type
            parameterized_return_object[parameter_[0]] = parameter_[3](
                redis_value_ if redis_value_ is not None else 0
            )
        if parameter_[2] == _DataSource.LITERAL:
            # parameter[3] is the type
            parameterized_return_object[parameter_[0]] = parameter_[3](parameter_[1])
    return parameterized_return_object


def export(
    qubits: List[str],
    couplers: List[str],
    output_path: Union[Path, str] = None,
) -> Dict[str, Any]:
    """
    Export a calibration seed file

    Args:
        output_path: Path to write the output to
        qubits: List of qubit ids to export
        couplers: List of couplers to export
    """
    return_object = {
        "calibration_config": {
            "qubit": [],
            "readout_resonator": [],
            "coupler": [],
            "discriminators": {"lda": {}},
        }
    }

    for qubit in qubits:
        # Iterate over qubit parameters
        return_object["calibration_config"]["qubit"].append(
            _assemble_parameters(_qubit_parameters, qubit)
        )

        # Iterate over readout resonator parameters
        return_object["calibration_config"]["readout_resonator"].append(
            _assemble_parameters(_readout_resonator_parameters, qubit)
        )

        # Iterate over discriminator parameters
        return_object["calibration_config"]["discriminators"]["lda"][qubit] = (
            _assemble_parameters(_lda_parameters, qubit, set_id=False)
        )

    for coupler in couplers:
        return_object["calibration_config"]["coupler"].append(
            _assemble_parameters(_coupler_parameters, coupler, redis_prefix="couplers")
        )

    # Save to output in case
    if output_path is not None:

        # Load template
        template_path_ = Path(__file__).parent.joinpath(
            "calibration_seed_template.toml"
        )
        with open(template_path_, "r") as f_:
            calibration_seed = tomlkit.load(f_)

        # Update values
        calibration_seed = _deep_update(calibration_seed, return_object)  # type: ignore

        # Save to output file
        with open(output_path, "w") as f_:
            tomlkit.dump(calibration_seed, f_)

    return return_object
