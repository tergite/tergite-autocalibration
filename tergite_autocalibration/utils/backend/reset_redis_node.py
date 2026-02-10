# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (c) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2025
# (C) Copyright Chalmers Next Labs AB 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from pathlib import Path
from typing import List

from tergite_autocalibration.config.globals import REDIS_CONNECTION, CONFIG
from tergite_autocalibration.lib.utils.node_factory import NodeFactory
from tergite_autocalibration.lib.utils.reflections import (
    find_inheriting_classes_ast_recursive,
)
from tergite_autocalibration.utils.logging import logger
from tergite_autocalibration.utils.misc.reflections import get_class_attributes


def reset_all_redis_nodes() -> None:
    node_factory = NodeFactory()
    node_names = node_factory.all_node_names()
    reset_redis_nodes(node_names)


def reset_redis_nodes(node_names: List[str]) -> None:
    qubits = CONFIG.run.qubits
    couplers = CONFIG.run.couplers

    node_factory = NodeFactory()

    node_implementation_paths = find_inheriting_classes_ast_recursive(
        Path(__file__).parent.parent.parent / "lib" / "nodes"
    )

    for node_name in node_names:
        node_cls_name = node_factory.node_name_mapping[node_name]
        node_implementation_path = node_implementation_paths[node_cls_name]

        node_cls_attributes = get_class_attributes(
            node_implementation_path, node_cls_name
        )

        logger.status(f"Resetting node: {node_name}")
        if "qubit_qois" in node_cls_attributes.keys():
            for qubit in qubits:
                redis_prefix_ = f"transmons:{qubit}"
                for qoi in node_cls_attributes["qubit_qois"]:
                    REDIS_CONNECTION.hset(redis_prefix_, qoi, "nan")
                    if "motzoi" in qoi:
                        REDIS_CONNECTION.hset(redis_prefix_, qoi, "0")
                    if "measure_3state_opt:pulse_amp" in qoi:
                        REDIS_CONNECTION.hset(redis_prefix_, qoi, "0")
                    if "measure_2state_opt:pulse_amp" in qoi:
                        REDIS_CONNECTION.hset(redis_prefix_, qoi, "0")
                REDIS_CONNECTION.hset(f"cs:{qubit}", node_name, "not_calibrated")
        if "coupler_qois" in node_cls_attributes.keys():
            for coupler in couplers:
                redis_prefix_ = f"couplers:{coupler}"
                for coupler_qoi in node_cls_attributes["coupler_qois"]:
                    REDIS_CONNECTION.hset(redis_prefix_, coupler_qoi, "nan")
                REDIS_CONNECTION.hset(f"cs:{coupler}", node_name, "not_calibrated")
