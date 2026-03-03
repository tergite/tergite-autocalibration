# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024, 2025, 2026
# (c) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
from typing import Union

import toml

import tergite_autocalibration
from tergite_autocalibration.config.globals import CONFIG, REDIS_CONNECTION
from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.base.node import QubitNode
from tergite_autocalibration.lib.utils.node_factory import NodeFactory
from tergite_autocalibration.utils.backend.redis_utils import (
    populate_initial_parameters,
    populate_node_parameters,
    revert_node_parameters,
    populate_quantities_of_interest,
)


def test_populate_inital_parameters():

    REDIS_CONNECTION.flushall()
    assert not REDIS_CONNECTION.keys()

    device = CONFIG.device
    qubits = device.qubits.keys()
    couplers = device.couplers.keys()
    populate_initial_parameters(qubits, couplers, REDIS_CONNECTION)
    redis_keys = REDIS_CONNECTION.keys()

    # test that all device elements are on redis
    for qubit in qubits:
        assert f"transmons:{qubit}" in redis_keys
    for coupler in couplers:
        assert f"couplers:{coupler}" in redis_keys

    # test values are correctly uploaded onto redis
    ro_config_ruration = device.qubits["q00"]["measure"]["pulse_duration"]
    ro_redis_duration = float(
        REDIS_CONNECTION.hget("transmons:q00", "measure:pulse_duration")
    )
    assert ro_config_ruration == ro_redis_duration
    cz_amplitude_redis = float(
        REDIS_CONNECTION.hget("couplers:q00_q01", "cz_pulse_amplitude")
    )
    cz_amplitude_config = device.couplers["q00_q01"]["cz_pulse_amplitude"]
    assert cz_amplitude_redis == cz_amplitude_config


def test_populate_node_parameters():

    REDIS_CONNECTION.flushall()
    assert not REDIS_CONNECTION.keys()

    device = CONFIG.device
    qubits = device.qubits.keys()
    couplers = device.couplers.keys()
    populate_node_parameters(
        "resonator_spectroscopy", False, qubits, couplers, REDIS_CONNECTION
    )

    # test node config values are correctly uploaded onto redis
    transmon_configuration = toml.load(CONFIG.node)
    node_config = transmon_configuration["resonator_spectroscopy"]["all"]
    reset_duration_config = node_config["reset"]["duration"]
    reset_duration_redis = float(
        REDIS_CONNECTION.hget("transmons:q00", "reset:duration")
    )
    assert reset_duration_config == reset_duration_redis


def test_revert_node_parameters():

    REDIS_CONNECTION.flushall()
    assert not REDIS_CONNECTION.keys()

    device = CONFIG.device
    qubits = device.qubits.keys()
    initial_qubit_parameters = device.qubits
    node = "resonator_spectroscopy"

    # flush the duration value
    REDIS_CONNECTION.hset("transmons:q00", "reset:duration", "nan")

    revert_node_parameters(node, qubits, REDIS_CONNECTION)
    reset_duration_redis = float(
        REDIS_CONNECTION.hget("transmons:q00", "reset:duration")
    )
    initial_reset_value = initial_qubit_parameters["q00"]["reset"]["duration"]

    assert reset_duration_redis == initial_reset_value


def test_populate_quantities_of_interest():
    """
    Iterate over all nodes in the factory and check whether they correctly push qois to redis
    """

    REDIS_CONNECTION.flushall()
    assert not REDIS_CONNECTION.keys()

    node_factory = NodeFactory()
    for node_name in node_factory.all_node_names():
        REDIS_CONNECTION.flushall()
        assert not REDIS_CONNECTION.keys()

        populate_quantities_of_interest(
            node_name, node_factory, ["q00", "q01"], ["q00_q01"], REDIS_CONNECTION
        )

        node_cls: Union["QubitNode", "CouplerNode"] = node_factory.get_node_class(
            node_name
        )

        if hasattr(node_cls, "qubit_qois"):
            for qubit_qoi in node_cls.qubit_qois:
                assert REDIS_CONNECTION.hexists("transmons:q00", qubit_qoi)

        if hasattr(node_cls, "coupler_qois"):
            for coupler_qoi in node_cls.coupler_qois:
                assert REDIS_CONNECTION.hexists("couplers:q00_q01", coupler_qoi)
