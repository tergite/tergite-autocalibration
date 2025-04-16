# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
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

import itertools
from typing import TYPE_CHECKING, ClassVar

from tergite_autocalibration.config.globals import REDIS_CONNECTION, CONFIG
from tergite_autocalibration.lib.base.node import CouplerNode, QubitNode
from tergite_autocalibration.utils.logging import logger
from tergite_autocalibration.lib.utils.node_factory import NodeFactory
from tergite_autocalibration.tools.mss.convert import structured_redis_storage

if TYPE_CHECKING:
    from tergite_autocalibration.lib.base.node import BaseNode


# NOTE: does this need to be a class?
class ResetRedisNode:
    node_factory = NodeFactory()
    node_names = node_factory.all_node_names()
    factory_dict = None

    def __init__(self):
        self.qubits = CONFIG.run.qubits
        self.couplers = CONFIG.run.couplers

        self.factory_dict: ClassVar[str, type["BaseNode"]] = {
            node_name: self.node_factory.get_node_class(node_name)
            for node_name in self.node_names
        }

        qois = [
            self.factory_dict[node].qubit_qois
            for node in self.node_names
            if issubclass(self.factory_dict[node], QubitNode)
        ]
        qois = [qoi for qoi in qois if qoi is not None]  # filter out Nones
        self.quantities_of_interest = list(itertools.chain.from_iterable(qois))
        coupler_qois = [
            self.factory_dict[node].coupler_qois
            for node in self.node_names
            if issubclass(self.factory_dict[node], CouplerNode)
        ]
        coupler_qois = [
            qoi for qoi in coupler_qois if qoi is not None
        ]  # filter out Nones
        self.coupler_quantities_of_interest = list(
            itertools.chain.from_iterable(coupler_qois)
        )

    def reset_node(self, remove_node):
        logger.status(f"{ remove_node = }")
        if issubclass(self.factory_dict[remove_node], QubitNode):
            self.reset_defined_fields_in_qubit_node(remove_node)
        if issubclass(self.factory_dict[remove_node], CouplerNode):
            self.reset_defined_fields_in_coupler_node(remove_node)

    def reset_all_nodes(self):
        self.reset_all_fields_in_qubit_nodes()
        self.reset_all_fields_in_coupler_nodes()

    def reset_defined_fields_in_qubit_node(self, remove_node):
        remove_fields = self.factory_dict[remove_node].qubit_qois
        for qubit in self.qubits:
            key = f"transmons:{qubit}"
            cs_key = f"cs:{qubit}"
            for field in remove_fields:
                REDIS_CONNECTION.hset(key, field, "nan")
                structured_redis_storage(key, qubit.strip("q"), None)
                if "motzoi" in field:
                    REDIS_CONNECTION.hset(key, field, "0")
                    structured_redis_storage(key, qubit.strip("q"), 0)
                if "measure_3state_opt:pulse_amp" in field:
                    REDIS_CONNECTION.hset(key, field, "0")
                    structured_redis_storage(key, qubit.strip("q"), 0)
                if "measure_2state_opt:pulse_amp" in field:
                    REDIS_CONNECTION.hset(key, field, "0")
                    structured_redis_storage(key, qubit.strip("q"), 0)
            REDIS_CONNECTION.hset(cs_key, remove_node, "not_calibrated")

    def reset_all_fields_in_qubit_nodes(self):
        for qubit in self.qubits:
            key = f"transmons:{qubit}"
            cs_key = f"cs:{qubit}"
            fields = REDIS_CONNECTION.hgetall(f"transmons:{qubit}").keys()
            for field in fields:
                REDIS_CONNECTION.hset(key, field, "nan")
                structured_redis_storage(key, qubit.strip("q"), None)
                if "motzoi" in field:
                    REDIS_CONNECTION.hset(key, field, "0")
                    structured_redis_storage(key, qubit.strip("q"), 0)
                if "measure_3state_opt:pulse_amp" in field:
                    REDIS_CONNECTION.hset(key, field, "0")
                    structured_redis_storage(key, qubit.strip("q"), 0)
                if "measure_2state_opt:pulse_amp" in field:
                    REDIS_CONNECTION.hset(key, field, "0")
                    structured_redis_storage(key, qubit.strip("q"), 0)
            for node in self.node_names:
                if issubclass(self.factory_dict[node], QubitNode):
                    REDIS_CONNECTION.hset(cs_key, node, "not_calibrated")

    def reset_defined_fields_in_coupler_node(self, remove_node):
        remove_fields = self.factory_dict[remove_node].coupler_qois
        for coupler in self.couplers:
            key = f"couplers:{coupler}"
            cs_key = f"cs:{coupler}"
            for field in remove_fields:
                REDIS_CONNECTION.hset(key, field, "nan")
                structured_redis_storage(key, coupler, None)
            REDIS_CONNECTION.hset(cs_key, remove_node, "not_calibrated")

    def reset_all_fields_in_coupler_nodes(self):
        for coupler in self.couplers:
            key = f"couplers:{coupler}"
            cs_key = f"cs:{coupler}"
            fields = REDIS_CONNECTION.hgetall(f"couplers:{coupler}").keys()
            for field in fields:
                REDIS_CONNECTION.hset(key, field, "nan")
                structured_redis_storage(key, coupler, None)
            for node in self.node_names:
                if issubclass(self.factory_dict[node], CouplerNode):
                    REDIS_CONNECTION.hset(cs_key, node, "not_calibrated")
