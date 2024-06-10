import tergite_acl.utils.user_input as ui
import numpy as np
from tergite_acl.scripts.calibration_supervisor import CalibrationSupervisor
from tergite_acl.lib.nodes import graph as cg, characterization_nodes as calibrate_nodes
from tergite_acl.utils.user_input import qubits,couplers
from tergite_acl.utils.reset_redis_node import ResetRedisNode
import optuna
from ipaddress import ip_address, IPv4Address
from tergite_acl.config.settings import CLUSTER_IP
from tergite_acl.scripts.calibration_supervisor import CalibrationSupervisor
from tergite_acl.scripts.db_backend_update import update_mss
from tergite_acl.utils.enums import ClusterMode
from tergite_acl.config.settings import CLUSTER_IP, REDIS_CONNECTION, CLUSTER_NAME

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
        cluster_mode: 'ClusterMode' = ClusterMode.real
        parsed_cluster_ip: 'IPv4Address' = CLUSTER_IP
        self.supervisor = CalibrationSupervisor(cluster_mode=cluster_mode,
                                    cluster_ip=parsed_cluster_ip)
        self.cxn = REDIS_CONNECTION
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
        self.node = node
        if node is None:
            self.all_results = self.supervisor.calibrate_node(self.node_park, **kwargs)
        else:
            self.all_results = self.supervisor.calibrate_node(node, **kwargs)
            self.node_park = node

    def next_node(self, node:str=None):
        if node is None:
            node = self.node_park
        print(cg[node])

    def get_name(self):
        return self.all_results[0].split('/')[-1]

    def get_results(self):
        return self.all_results[1]

class OptimizeNode:
    def __init__(self, node, trails = 50, params = ['cz_pulse_frequency','cz_pulse_duration','cz_pulse_amplitude']):
        self.monitor = Monitor()
        self.reset_redis = ResetRedisNode()
        self.node = node
        self.qubits = qubits
        self.couplers = couplers
        sampler = optuna.samplers.CmaEsSampler(with_margin=True)
        self.study = optuna.create_study(sampler=sampler)
        self.trails = trails
        self.params = params

    def objective_cz(self,trial):
        
        freqs_dict, times_dict, amps_dict = None, None, None
        for param in self.params:
            if param == 'cz_pulse_frequency':
                freqs = np.array([trial.suggest_float("cz_pulse_frequency", -2, 2,step=0.001)])*1e6
                freqs_dict = dict(zip(couplers,freqs))
            elif param == 'cz_pulse_duration':
                times = np.array([trial.suggest_float("cz_pulse_duration", -20, 20,step=0.01)])*1e-9
                times_dict = dict(zip(couplers,times))
            elif param == 'cz_pulse_amplitude':
                amps = np.array([trial.suggest_float("cz_pulse_amplitude", -0.02, 0.02,step=0.00001)])
                amps_dict = dict(zip(couplers,amps))
        print(f"Optimizing {self.node} with {freqs_dict}, {times_dict}, {amps_dict}")
        self.monitor.calibrate_node(self.node, opt_cz_pulse_frequency = freqs_dict,
                                                        opt_cz_pulse_duration = times_dict,
                                                        opt_cz_pulse_amplitude = amps_dict)
        results = self.monitor.get_results()
        all_results = [results[coupler] for coupler in results.keys()][:len(results.keys())-1]
        if self.node[-4:] == 'ssro':
            all_costs = [ np.sqrt(((res['cz_phase']-180)/180)**2 + res['cz_pop_loss']**2+res['cz_leakage']**2) for res in all_results]
        else:
            all_costs = [ np.sqrt(((res['cz_phase']-180)/180)**2 + res['cz_pop_loss']**2) for res in all_results]
        return sum(all_costs)

    def optimize_node(self):
        print(f"Optimizing {self.node} with {self.trails} trails")
        self.study.optimize(self.objective_cz, n_trials=self.trails)
        self.best_params = self.study.best_params
        print(f"Validating trail {self.study.best_trial.number} with params {self.best_params}")
        self.validate_cz()

        print(f"Optimization finished for {self.node}")
        return self.study

    def plot_optimization(self):
        return optuna.visualization.plot_optimization_history(self.study)

    def validate_cz(self, best_params = None):
        if best_params is None:
            best_params = self.best_params
        # freqs = np.array([best_params['cz_pulse_frequency']])*1e6
        # times = np.array([best_params['cz_pulse_duration']])*1e-9
        # amps = np.array([best_params['cz_pulse_amplitude']])

        freqs_dict, times_dict, amps_dict = None, None, None
        for param in self.params:
            if param == 'cz_pulse_frequency':
                freqs = np.array([best_params['cz_pulse_frequency']])*1e6
                freqs_dict = dict(zip(couplers,freqs))
            elif param == 'cz_pulse_duration':
                times = np.array([best_params['cz_pulse_duration']])*1e-9
                times_dict = dict(zip(couplers,times))
            elif param == 'cz_pulse_amplitude':
                amps = np.array([best_params['cz_pulse_amplitude']])
                amps_dict = dict(zip(couplers,amps))

        self.monitor.calibrate_node(self.node, opt_cz_pulse_frequency = freqs_dict,
                                                        opt_cz_pulse_duration = times_dict,
                                                        opt_cz_pulse_amplitude = amps_dict)
        results = self.monitor.get_results()
        print(results)
        return results

# monitor = Monitor()
