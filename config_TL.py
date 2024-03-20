from importlib import reload
import utilities.user_input as ui
import numpy as np
import workers.calibration_supervisor as supervisor
import nodes
from nodes import node as calibrate_nodes
from nodes.graph import graph as cg
import workers
import overnight

qubits_10 = [f"q{i}" for i in range(16, 26)]

class UserInputObject:
    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = "__" + name

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name, None)
    
    def __set__(self, obj, value):
        value_old = self.__get__(obj)
        if value_old is None:
            assert len(set(value)) == len(value), f"The value of {self.public_name} cannot contain same elements."
            setattr(obj, self.private_name, value)
        else:
            value_old[:] = [v for v in value_old if v in value]
            for v in value:
                if v not in value_old:
                    value_old.append(v)
            value_old.sort()
            
class Monitor:

    qubits = UserInputObject()
    couplers = UserInputObject()

    def __init__(self):
        self.qubits = ui.qubits
        self.couplers = ui.couplers
        self.nodes = [(f.split("_Node")[0]).lower() for f in dir(calibrate_nodes) if f.endswith("_Node")]
        self.cxn = supervisor.redis_connection
        self.node_park = "resonator_spectroscopy"

    def __repr__(self):
        return "Calibration Monitor @@\n--------------\n" \
            + f"Parking node: {self.node_park} \n Qubits: \n\t {self.qubits} \n Couplers: \n\t {self.couplers}"

    def node_status(self, node:str=None):
        if node is None: node = self.node_park
        print("Qubits:")
        for qubit in self.qubits:
            print(f"    {qubit}: {node}:", self.cxn.hget(f"cs:{qubit}", node))
        print("-----------------------")
        print("Couplers:")
        for coupler in self.couplers:
            print(f"    {coupler}: {node}:", self.cxn.hget(f"cs:{coupler}", node))

    def calibrate_node(self, node:str=None, **kwargs):
        if node is None:
            self.all_results = supervisor.calibrate_node(self.node_park, **kwargs)    
        else:
            self.all_results = supervisor.calibrate_node(node, **kwargs)
            self.node_park = node

    def next_node(self, node:str=None):
        if node is None:
            node = self.node_park
        print(cg[node])

    def get_results(self):
        return self.all_results[1]
    
    def get_node_name(self):
        return str(self.all_results[0]).split('/')[-1]
        
# monitor = Monitor()