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

import toml

from tergite_autocalibration.config.calibration import CONFIG
from tergite_autocalibration.config.settings import QOI_CONFIG, REDIS_CONNECTION
from tergite_autocalibration.lib.utils.node_factory import NodeFactory
from tergite_autocalibration.tools.mss.convert import structured_redis_storage


class ResetRedisNode:
    def __init__(self):
        self.qubits = CONFIG.qubits
        self.couplers = CONFIG.couplers
        node_factory = NodeFactory()
        self.nodes = node_factory.all_nodes()
        qoi_configuration = toml.load(QOI_CONFIG)
        self.quantities_of_interest = qoi_configuration["qoi"]["qubits"]
        self.coupler_quantities_of_interest = qoi_configuration["qoi"]["couplers"]

    def reset_node(self, remove_node):
        print(f"{ remove_node = }")
        if not remove_node == "all":
            if remove_node in self.quantities_of_interest:
                remove_fields = self.quantities_of_interest[remove_node].keys()
            elif remove_node in self.coupler_quantities_of_interest:
                remove_fields = self.coupler_quantities_of_interest[remove_node].keys()
            else:
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
                for node in self.nodes:
                    REDIS_CONNECTION.hset(cs_key, node, "not_calibrated")
            elif remove_node in self.nodes:
                for field in remove_fields:
                    REDIS_CONNECTION.hset(key, field, "nan")
                    structured_redis_storage(key, qubit.strip("q"), None)
                    if "motzoi" in field:
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
                for node in self.nodes:
                    REDIS_CONNECTION.hset(cs_key, node, "not_calibrated")
            elif remove_node in self.nodes:
                for field in remove_fields:
                    REDIS_CONNECTION.hset(key, field, "nan")
                    structured_redis_storage(key, coupler, None)
                REDIS_CONNECTION.hset(cs_key, remove_node, "not_calibrated")
            else:
                raise ValueError("Invalid Field")
