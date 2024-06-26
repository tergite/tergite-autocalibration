import toml

from tergite_autocalibration.config.settings import DEVICE_CONFIG, REDIS_CONNECTION
from tergite_autocalibration.lib.node_factory import NodeFactory
from tergite_autocalibration.utils import user_input
from tergite_autocalibration.utils.convert import structured_redis_storage


class ResetRedisNode:
    def __init__(self):
        self.qubits = user_input.qubits
        self.couplers = user_input.couplers
        node_factory = NodeFactory()
        self.nodes = node_factory.all_nodes()
        transmon_configuration = toml.load(DEVICE_CONFIG)
        self.quantities_of_interest = transmon_configuration['qoi']['qubits']
        self.coupler_quantities_of_interest = transmon_configuration['qoi']['couplers']

    def reset_node(self, remove_node):
        print(f'{ remove_node = }')
        if not remove_node == 'all':
            if remove_node in self.quantities_of_interest:
                remove_fields = self.quantities_of_interest[remove_node].keys()
            elif remove_node in self.coupler_quantities_of_interest:
                remove_fields = self.coupler_quantities_of_interest[remove_node].keys()
            else:
                raise ValueError(f'{remove_node} is not present in the list of qois')

        # TODO Why flush?
        # red.flushdb()
        for qubit in self.qubits:
            fields = REDIS_CONNECTION.hgetall(f'transmons:{qubit}').keys()
            key = f'transmons:{qubit}'
            cs_key = f'cs:{qubit}'
            if remove_node == 'all':
                for field in fields:
                    REDIS_CONNECTION.hset(key, field, 'nan')
                    structured_redis_storage(key, qubit.strip('q'), None)
                    if 'motzoi' in field:
                        REDIS_CONNECTION.hset(key, field, '0')
                        structured_redis_storage(key, qubit.strip('q'), 0)
                for node in self.nodes:
                    REDIS_CONNECTION.hset(cs_key, node, 'not_calibrated')
            elif remove_node in self.nodes:
                for field in remove_fields:
                    REDIS_CONNECTION.hset(key, field, 'nan')
                    structured_redis_storage(key, qubit.strip('q'), None)
                    if 'motzoi' in field:
                        REDIS_CONNECTION.hset(key, field, '0')
                        structured_redis_storage(key, qubit.strip('q'), 0)
                REDIS_CONNECTION.hset(cs_key, remove_node, 'not_calibrated')
            else:
                raise ValueError('Invalid Field')

        for coupler in self.couplers:
            fields = REDIS_CONNECTION.hgetall(f'couplers:{coupler}').keys()
            key = f'couplers:{coupler}'
            cs_key = f'cs:{coupler}'
            if remove_node == 'all':
                for field in fields:
                    REDIS_CONNECTION.hset(key, field, 'nan')
                    structured_redis_storage(key, coupler, None)
                for node in self.nodes:
                    REDIS_CONNECTION.hset(cs_key, node, 'not_calibrated')
            elif remove_node in self.nodes:
                for field in remove_fields:
                    REDIS_CONNECTION.hset(key, field, 'nan')
                    structured_redis_storage(key, coupler, None)
                REDIS_CONNECTION.hset(cs_key, remove_node, 'not_calibrated')
            else:
                raise ValueError('Invalid Field')
