import redis
import toml
import argparse
from utilities import user_input
from nodes.node import NodeFactory

class ResetRedisNode:
    def __init__(self):
        self.red = redis.Redis(decode_responses=True)
        self.qubits = user_input.qubits
        self.couplers = user_input.couplers
        node_factory = NodeFactory()
        self.nodes = node_factory.all_nodes()
        transmon_configuration = toml.load('./config_files/device_config.toml')
        self.quantities_of_interest = transmon_configuration['qoi']['qubits']
        self.coupler_quantities_of_interest = transmon_configuration['qoi']['couplers']

    def reset_node(self,remove_node):
        print(f'{ remove_node = }')
        if not remove_node == 'all':
            if remove_node in self.quantities_of_interest:
                remove_fields = self.quantities_of_interest[remove_node].keys()
            elif remove_node in self.coupler_quantities_of_interest:
                remove_fields = self.coupler_quantities_of_interest[remove_node].keys()

        #TODO Why flush?
        #red.flushdb()
        for qubit in self.qubits:
            fields =  self.red.hgetall(f'transmons:{qubit}').keys()
            key = f'transmons:{qubit}'
            cs_key = f'cs:{qubit}'
            if remove_node == 'all':
                for field in fields:
                    self.red.hset(key, field, 'nan' )
                for node in self.nodes:
                    self.red.hset(cs_key, node, 'not_calibrated' )
            elif remove_node in self.nodes:
                for field in remove_fields:
                    self.red.hset(key, field, 'nan')
                self.red.hset(cs_key, remove_node, 'not_calibrated' )
            else:
                raise ValueError('Invalid Field')

        for coupler in self.couplers:
            fields =  self.red.hgetall(f'couplers:{coupler}').keys()
            key = f'couplers:{coupler}'
            cs_key = f'cs:{coupler}'
            if remove_node == 'all':
                for field in fields:
                    self.red.hset(key, field, 'nan' )
                for node in self.nodes:
                    self.red.hset(cs_key, node, 'not_calibrated' )
            elif remove_node in self.nodes:
                for field in remove_fields:
                    self.red.hset(key, field, 'nan')
                self.red.hset(cs_key, remove_node, 'not_calibrated' )
            else:
                raise ValueError('Invalid Field')
