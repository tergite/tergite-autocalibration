from importlib import reload
import tergite_acl.utilities.user_input as ui
import numpy as np
import tergite_acl.workers.calibration_supervisor as supervisor
import nodes
from tergite_acl.nodes import node as calibrate_nodes
from tergite_acl.nodes.graph import graph as cg
import workers
import overnight
from tergite_acl.utilities.user_input import qubits,couplers
from tergite_acl.utilities.reset_redis_node import ResetRedisNode
import optuna

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
        return self.all_results

class OptimizeNode:
    def __init__(self, node):
        self.monitor = Monitor()
        self.reset_redis = ResetRedisNode()
        self.node = node
        self.qubits = qubits
        self.couplers = couplers
        sampler = optuna.samplers.CmaEsSampler(with_margin=True)
        self.study = optuna.create_study(sampler=sampler)

    def objective_cz(self,trial):
        freqs = np.array([trial.suggest_float("freq", -1, 1,step=0.01)])*1e6
        times = np.array([trial.suggest_float("time", -10, 10,step=0.1)])*1e-9
        amps = np.array([trial.suggest_float("amp", -0.01, 0.01,step=0.001)])
        # self.reset_redis.reset_node(self.node)
        self.monitor.calibrate_node(self.node, opt_cz_pulse_frequency = dict(zip(couplers,freqs)),
                                                        opt_cz_pulse_duration = dict(zip(couplers,times)),
                                                        opt_cz_pulse_amplitude = dict(zip(couplers,amps)))
        results = self.monitor.get_results()
        all_results = [results[coupler] for coupler in self.couplers]
        all_costs = [ ((np.abs(res['cz_phase'])-180)/180)**2 + res['cz_pop_loss']**2+res['cz_leakage']**2 for res in all_results]
        return sum(all_costs)

    def optimize_node(self):
        print(f"Optimizing {self.node}")
        self.study.optimize(self.objective_cz, n_trials=50)
        self.best_params = self.study.best_params
        print(f"Validating trail {self.study.best_trial.number} with params {self.best_params}")
        self.validate_cz()

        print(f"Optimization finished for {self.node}")
        return self.study

    def plot_optimization(self):
        return optuna.visualization.plot_optimization_history(self.study)

    def validate_cz(self,best_params = self.best_params):
        freqs = np.array([best_params['freq']])*1e6
        times = np.array([best_params['time']])*1e-9
        amps = np.array([best_params['amp']])
        self.monitor.calibrate_node('cz_calibration_ssro',opt_cz_pulse_frequency = dict(zip(couplers,freqs)),
                                                        opt_cz_pulse_duration = dict(zip(couplers,times)),
                                                        opt_cz_pulse_amplitude = dict(zip(couplers,amps)))
        results = self.monitor.get_results()
        print(results)
        return results

# monitor = Monitor()
