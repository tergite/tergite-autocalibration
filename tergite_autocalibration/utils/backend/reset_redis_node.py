# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (c) Copyright Stefan Hill 2024
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

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.config.legacy import LEGACY_CONFIG
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
        self.qubits = LEGACY_CONFIG.qubits
        self.couplers = LEGACY_CONFIG.couplers

        self.factory_dict: ClassVar[str, type["BaseNode"]] = {
            node_name: self.node_factory.get_node_class(node_name)
            for node_name in self.node_names
        }

        qois = [self.factory_dict[node].qubit_qois for node in self.node_names]
        qois = [qoi for qoi in qois if qoi is not None]  # filter out Nones
        self.quantities_of_interest = list(itertools.chain.from_iterable(qois))
        coupler_qois = [
            self.factory_dict[node].coupler_qois for node in self.node_names
        ]
        coupler_qois = [
            qoi for qoi in coupler_qois if qoi is not None
        ]  # filter out Nones
        self.coupler_quantities_of_interest = list(
            itertools.chain.from_iterable(coupler_qois)
        )

    def reset_node(self, remove_node):
        print(f"{ remove_node = }")
        if not remove_node == "all":
            remove_fields = self.factory_dict[remove_node].qubit_qois
            if remove_fields is None:
                remove_fields = self.factory_dict[remove_node].coupler_qois
            if remove_fields is None:
                raise ValueError(f"{remove_node} is not present in the list of qois")

        # TODO Why flush?
        # red.flushdb()
        for qubit in self.qubits:
            fields = REDIS_CONNECTION.hgetall(f"transmons:{qubit}").keys()
            key = f"transmons:{qubit}"
            cs_key = f"cs:{qubit}"
            if remove_node == "all":
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
                    REDIS_CONNECTION.hset(cs_key, node, "not_calibrated")
            elif remove_node in self.node_names:
                for field in remove_fields:
                    REDIS_CONNECTION.hset(key, field, "nan")
                    structured_redis_storage(key, qubit.strip("q"), None)
                    if "motzoi" in field:
                        REDIS_CONNECTION.hset(key, field, "0")
                        structured_redis_storage(key, qubit.strip("q"), 0)
                    if "measure_3state_opt:pulse_amp" in field:
                        REDIS_CONNECTION.hset(key, field, "0")
                        structured_redis_storage(key, qubit.strip("q"), 0)
                REDIS_CONNECTION.hset(cs_key, remove_node, "not_calibrated")
            else:
                raise ValueError("Invalid Field")

        for coupler in self.couplers:
            fields = REDIS_CONNECTION.hgetall(f"couplers:{coupler}").keys()
            key = f"couplers:{coupler}"
            cs_key = f"cs:{coupler}"
            if remove_node == "all":
                for field in fields:
                    REDIS_CONNECTION.hset(key, field, "nan")
                    structured_redis_storage(key, coupler, None)
                for node in self.node_names:
                    REDIS_CONNECTION.hset(cs_key, node, "not_calibrated")
            elif remove_node in self.node_names:
                for field in remove_fields:
                    REDIS_CONNECTION.hset(key, field, "nan")
                    structured_redis_storage(key, coupler, None)
                REDIS_CONNECTION.hset(cs_key, remove_node, "not_calibrated")
            else:
                raise ValueError("Invalid Field")
