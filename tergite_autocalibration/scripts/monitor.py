# This code is part of Tergite
#
# (C) Copyright Tong Liu 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from ipaddress import IPv4Address

import numpy as np
import optuna

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.config.legacy import LEGACY_CONFIG
from tergite_autocalibration.config.settings import CLUSTER_IP
from tergite_autocalibration.lib.nodes import (
    characterization_nodes as calibrate_nodes,
)
from tergite_autocalibration.lib.utils import graph as cg
from tergite_autocalibration.scripts.calibration_supervisor import CalibrationSupervisor
from tergite_autocalibration.utils.backend.reset_redis_node import ResetRedisNode
from tergite_autocalibration.utils.dto.enums import MeasurementMode

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
            assert len(set(value)) == len(
                value
            ), f"The value of {self.public_name} cannot contain same elements."
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
        self.qubits = LEGACY_CONFIG.qubits
        self.couplers = LEGACY_CONFIG.couplers
        self.nodes = [
            (f.split("_Node")[0]).lower()
            for f in dir(calibrate_nodes)
            if f.endswith("_Node")
        ]
        cluster_mode: "MeasurementMode" = MeasurementMode.real
        parsed_cluster_ip: "IPv4Address" = CLUSTER_IP
        self.supervisor = CalibrationSupervisor(
            measurement_mode=cluster_mode, cluster_ip=parsed_cluster_ip
        )
        self.cxn = REDIS_CONNECTION
        self.node_park = self.supervisor.node_factory.create_node.create_node(
            "resonator_spectroscopy", self.qubits, couplers=self.couplers
        )

    def __repr__(self):
        return (
            "Calibration Monitor @@\n--------------\n"
            + f"Parking node: {self.node_park.name} \n Qubits: \n\t {self.qubits} \n Couplers: \n\t {self.couplers}"
        )

    def node_status(self, node: str = None):
        if node is None:
            node = self.node_park
        print("Qubits:")
        for qubit in self.qubits:
            print(f"    {qubit}: {node}:", self.cxn.hget(f"cs:{qubit}", node))
        print("-----------------------")
        print("Couplers:")
        for coupler in self.couplers:
            print(f"    {coupler}: {node}:", self.cxn.hget(f"cs:{coupler}", node))

    def calibrate_node(self, node: str = None, **kwargs):
        self.node = node
        if node is None:
            node = self.node_park
        node.calibrate(**kwargs)
        self.node_park = node

    def next_node(self, node: str = None):
        # TODO: How and when is this method called?
        if node is None:
            node = self.node_park
        print(cg[node])

    def get_name(self):
        return self.all_results[0].split("/")[-1]

    def get_results(self):
        return self.all_results[1]


class OptimizeNode:
    def __init__(
        self,
        node,
        trails=50,
        params=["cz_pulse_frequency", "cz_pulse_duration", "cz_pulse_amplitude"],
        optimize_swap=False,
    ):
        self.monitor = Monitor()
        self.reset_redis = ResetRedisNode()
        self.node = node
        self.qubits = LEGACY_CONFIG.qubits
        self.couplers = LEGACY_CONFIG.couplers
        sampler = optuna.samplers.CmaEsSampler(with_margin=True)
        self.study = optuna.create_study(sampler=sampler)
        self.trails = trails
        self.params = params
        self.optimize_swap = optimize_swap

    def objective_cz(self, trial):
        freqs_dict, times_dict, amps_dict = None, None, None
        for param in self.params:
            if param == "cz_pulse_frequency":
                freqs = (
                    np.array(
                        [trial.suggest_float("cz_pulse_frequency", -4, 4, step=0.001)]
                    )
                    * 1e6
                )
                freqs_dict = dict(zip(self.couplers, freqs))
            elif param == "cz_pulse_duration":
                times = (
                    np.array(
                        [trial.suggest_float("cz_pulse_duration", -20, 20, step=1)]
                    )
                    * 1e-9
                )
                times_dict = dict(zip(self.couplers, times))
            elif param == "cz_pulse_amplitude":
                amps = np.array(
                    [
                        trial.suggest_float(
                            "cz_pulse_amplitude", -0.04, 0.04, step=0.0001
                        )
                    ]
                )
                amps_dict = dict(zip(self.couplers, amps))
        print(f"Optimizing {self.node} with {freqs_dict}, {times_dict}, {amps_dict}")
        self.monitor.calibrate_node(
            "cz_calibration_ssro",
            opt_cz_pulse_frequency=freqs_dict,
            opt_cz_pulse_duration=times_dict,
            opt_cz_pulse_amplitude=amps_dict,
        )
        results = self.monitor.get_results()
        all_results1 = [results[coupler] for coupler in results.keys()][
            : len(results.keys()) - 1
        ]

        if self.optimize_swap:
            self.monitor.calibrate_node(
                "cz_calibration_swap_ssro",
                opt_cz_pulse_frequency=freqs_dict,
                opt_cz_pulse_duration=times_dict,
                opt_cz_pulse_amplitude=amps_dict,
            )
            results = self.monitor.get_results()
            all_results2 = [results[coupler] for coupler in results.keys()][
                : len(results.keys()) - 1
            ]

        if self.node[-4:] == "ssro":
            all_costs1 = [
                np.sqrt(
                    ((res["cz_phase"] - 180) / 180) ** 2
                    + res["cz_pop_loss"] ** 2
                    + res["cz_leakage"] ** 2
                )
                for res in all_results1
            ]
            if self.optimize_swap:
                all_costs2 = [
                    np.sqrt(
                        ((res["cz_phase"] - 180) / 180) ** 2
                        + res["cz_pop_loss"] ** 2
                        + res["cz_leakage"] ** 2
                    )
                    for res in all_results2
                ]
                all_costs = all_costs1 + all_costs2
            else:
                all_costs = all_costs1
        else:
            all_costs1 = [
                np.sqrt(((res["cz_phase"] - 180) / 180) ** 2 + res["cz_pop_loss"] ** 2)
                for res in all_results1
            ]
            if self.optimize_swap:
                all_costs2 = [
                    np.sqrt(
                        ((res["cz_phase"] - 180) / 180) ** 2
                        + (2 * res["cz_pop_loss"]) ** 2
                    )
                    for res in all_results2
                ]
                all_costs = all_costs1 + all_costs2
            else:
                all_costs = all_costs1

        return sum(all_costs)

    def optimize_node(self):
        print(f"Optimizing {self.node} with {self.trails} trails")
        self.study.optimize(self.objective_cz, n_trials=self.trails)
        self.best_params = self.study.best_params
        print(
            f"Validating trail {self.study.best_trial.number} with params {self.best_params}"
        )
        self.validate_cz()

        print(f"Optimization finished for {self.node}")
        return self.study

    def plot_optimization(self):
        return optuna.visualization.plot_optimization_history(self.study)

    def validate_cz(self, best_params=None):
        if best_params is None:
            best_params = self.best_params
        # freqs = np.array([best_params['cz_pulse_frequency']])*1e6
        # times = np.array([best_params['cz_pulse_duration']])*1e-9
        # amps = np.array([best_params['cz_pulse_amplitude']])

        freqs_dict, times_dict, amps_dict = None, None, None
        for param in self.params:
            if param == "cz_pulse_frequency":
                freqs = np.array([best_params["cz_pulse_frequency"]]) * 1e6
                freqs_dict = dict(zip(self.couplers, freqs))
            elif param == "cz_pulse_duration":
                times = np.array([best_params["cz_pulse_duration"]]) * 1e-9
                times_dict = dict(zip(self.couplers, times))
            elif param == "cz_pulse_amplitude":
                amps = np.array([best_params["cz_pulse_amplitude"]])
                amps_dict = dict(zip(self.couplers, amps))

        self.monitor.calibrate_node(
            "cz_calibrate_ssro",
            opt_cz_pulse_frequency=freqs_dict,
            opt_cz_pulse_duration=times_dict,
            opt_cz_pulse_amplitude=amps_dict,
        )
        self.monitor.calibrate_node(
            "cz_calibrate_swap_ssro",
            opt_cz_pulse_frequency=freqs_dict,
            opt_cz_pulse_duration=times_dict,
            opt_cz_pulse_amplitude=amps_dict,
        )
        results = self.monitor.get_results()
        print(results)
        return results


# monitor = Monitor()
