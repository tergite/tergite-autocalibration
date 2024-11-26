# This code is part of Tergite
#
# (C) Copyright Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


import datetime
import os
from pathlib import Path

import numpy as np
import optuna

from tergite_autocalibration.config.legacy import dh
from tergite_autocalibration.lib.base.schedule_node import ScheduleNode
from tergite_autocalibration.lib.nodes.characterization.randomized_benchmarking.analysis import (
    RandomizedBenchmarkingSSRONodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_calibration.node import (
    CZCalibrationSSRONode,
)
from tergite_autocalibration.lib.nodes.coupler.cz_dynamic_phase.node import (
    CZDynamicPhaseSSRONode,
    CZDynamicPhaseSwapSSRONode,
)
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.measurement import (
    TQGRandomizedBenchmarkingSSRO,
)
from tergite_autocalibration.lib.utils import redis

RB_REPEATS = 10


class TQGRandomizedBenchmarkingSSRONode(ScheduleNode):
    measurement_obj = TQGRandomizedBenchmarkingSSRO
    analysis_obj = RandomizedBenchmarkingSSRONodeAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits  # is this needed?
        self.couplers = couplers  # is this needed?
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.schedule_keywords = schedule_keywords
        self.coupled_qubits = couplers[0].split(sep="_")

        self.backup = False
        self.qubit_state = 2
        # TODO change it a dictionary like samplespace
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.external_samplespace = {
            "seeds": {
                coupler: np.arange(RB_REPEATS, dtype=np.int32)
                for coupler in self.couplers
            }
        }

        self.initial_schedule_samplespace = {
            "number_of_cliffords": {
                coupler: np.append(
                    np.array([0, 1, 2, 3, 4, 8, 10, 16, 22, 32, 64, 128]), [0, 1, 2]
                )
                for coupler in self.couplers
            },
        }

    def pre_measurement_operation(self, reduced_ext_space: dict):
        self.schedule_samplespace = (
            self.initial_schedule_samplespace | reduced_ext_space
        )

    @property
    def dimensions(self):
        return [
            len(
                self.initial_schedule_samplespace["number_of_cliffords"][
                    self.couplers[0]
                ]
            ),
            1,
        ]


class TQGRandomizedBenchmarkingInterleavedSSRONode(ScheduleNode):
    coupler_qois = ["tqg_fidelity_interleaved"]
    measurement_obj = TQGRandomizedBenchmarkingSSRO
    analysis_obj = RandomizedBenchmarkingSSRONodeAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.type = "parameterized_sweep"
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep="_")
        self.schedule_keywords = schedule_keywords
        self.backup = False

        self.qubit_state = 2
        self.schedule_keywords["interleaving_clifford_id"] = 4386
        self.schedule_keywords["qubit_state"] = self.qubit_state
        # TODO change it a dictionary like samplespace
        self.external_samplespace = {
            "seeds": {
                coupler: np.arange(RB_REPEATS, dtype=np.int32)
                for coupler in self.couplers
            }
        }

        self.initial_schedule_samplespace = {
            "number_of_cliffords": {
                coupler: np.append(
                    np.array([0, 1, 2, 3, 4, 8, 10, 16, 22, 32, 64, 128]), [0, 1, 2]
                )
                for coupler in self.couplers
            },
        }

    def pre_measurement_operation(self, reduced_ext_space: dict):
        self.schedule_samplespace = (
            self.initial_schedule_samplespace | reduced_ext_space
        )

    @property
    def dimensions(self):
        return [
            len(
                self.initial_schedule_samplespace["number_of_cliffords"][
                    self.couplers[0]
                ]
            ),
            1,
        ]


class CZRBOptimizeSSRONode(ScheduleNode):
    measurement_obj = TQGRandomizedBenchmarkingSSRO
    analysis_obj = RandomizedBenchmarkingSSRONodeAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        print("running cz rb ssro optimization node")
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.coupler = couplers[0]
        self.coupled_qubits = couplers[0].split(sep="_")
        self.edges = couplers
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.schedule_keywords = schedule_keywords
        self.schedule_keywords["qubit_state"] = self.qubit_state
        self.qubit_type_list = ["Control", "Target"]
        # if self.swap:
        #     qubit_type_list.reverse()
        self.redis_connection = redis.Redis(decode_responses=True)
        measurement_start = datetime.now()
        self.time_id = measurement_start.strftime("%Y%m%d_%H%M%S")
        self.log_path = "cz_optimization/" + self.time_id + "/"
        os.makedirs(self.log_path, exist_ok=True)

        sampler = optuna.samplers.CmaEsSampler(with_margin=True)
        self.study = optuna.create_study(
            sampler=sampler, study_name=self.name + "_" + self.time_id
        )
        self.average = False
        self.trails = 70
        self.opt_params = ["cz_duration", "cz_frequency"]
        self.full_params = ["cz_duration", "cz_frequency", "cz_amplitude"]
        self.all_results_list = []
        self.original_cz_param = self.redis_connection.hgetall(
            f"couplers:{self.coupler}"
        )

    def objective(self, trial):
        param_dict = {}
        for param in self.full_params:
            if param in self.opt_params:
                if param == "cz_duration":
                    values = (
                        np.array([trial.suggest_float("cz_duration", -25, 25, step=1)])
                        * 1e-9
                    )
                    param_dict[param] = dict(zip(self.couplers, values))
                elif param == "cz_frequency":
                    values = (
                        np.array(
                            [trial.suggest_float("cz_frequency", -2, 2, step=0.005)]
                        )
                        * 1e6
                    )
                    param_dict[param] = dict(zip(self.couplers, values))
                elif param == "cz_amplitude":
                    values = np.array(
                        [trial.suggest_float("cz_amplitude", -0.1, 0.1, step=0.001)]
                    )
                    param_dict[param] = dict(zip(self.couplers, values))
            else:
                param_dict[param] = None

        print(f"Optimizing {self.name} with {param_dict}")

        cz_param = self.redis_connection.hgetall(f"couplers:{self.coupler}")

        if param_dict["cz_frequency"] is not None:
            cz_param["cz_pulse_frequency"] = (
                float(cz_param["cz_pulse_frequency"])
                + param_dict["cz_frequency"][self.coupler]
            )
        if param_dict["cz_duration"] is not None:
            cz_param["cz_pulse_duration"] = (
                float(cz_param["cz_pulse_duration"])
                + param_dict["cz_duration"][self.coupler]
            )
        if param_dict["cz_amplitude"] is not None:
            cz_param["cz_pulse_amplitude"] = (
                float(cz_param["cz_pulse_amplitude"])
                + param_dict["cz_amplitude"][self.coupler]
            )

        print("cz_param is:", cz_param)

        for key, value in cz_param.items():
            self.redis_connection.hset(f"couplers:{self.coupler}", key, value)

        node_dynamic_phase = CZDynamicPhaseSSRONode(
            "cz_dynamic_phase", self.all_qubits, self.couplers
        )

        dynamic_phase = node_dynamic_phase.calibrate(
            self.data_path, self.lab_ic, self.cluster_status
        )

        node_dynamic_phase_swap = CZDynamicPhaseSwapSSRONode(
            "cz_dynamic_phase_swap", self.all_qubits, self.couplers
        )

        dynamic_phase_swap = node_dynamic_phase_swap.calibrate(
            self.data_path, self.lab_ic, self.cluster_status
        )
        # print('dynamic_pahse_results are: ', dynamic_phase_swap)

        coupler_append = "c" + self.couplers[0].replace("_", "")

        if (
            dh.get_legacy("qubit_types")[self.coupled_qubits[0]]
            == self.qubit_type_list[0]
        ):
            cz_param["cz_dynamic_target"] = (
                -1
                * dynamic_phase[self.coupled_qubits[1] + coupler_append][
                    "cz_dynamic_target"
                ]
            )
            cz_param["cz_dynamic_control"] = (
                -1
                * dynamic_phase_swap[self.coupled_qubits[0] + coupler_append][
                    "cz_dynamic_control"
                ]
            )
        else:
            cz_param["cz_dynamic_target"] = (
                -1
                * dynamic_phase[self.coupled_qubits[0] + coupler_append][
                    "cz_dynamic_target"
                ]
            )
            cz_param["cz_dynamic_control"] = (
                -1
                * dynamic_phase_swap[self.coupled_qubits[1] + coupler_append][
                    "cz_dynamic_control"
                ]
            )

        for key, value in cz_param.items():
            self.redis_connection.hset(f"couplers:{self.coupler}", key, value)

        rb_node = TQGRandomizedBenchmarkingInterleavedSSRONode(
            "tqg_randomized_benchmarking_interleaved_ssro",
            self.all_qubits,
            self.couplers,
        )

        tqg_rb_results = rb_node.calibrate(
            self.data_path, self.lab_ic, self.cluster_status
        )

        all_results = [
            tqg_rb_results[qubit + coupler_append] for qubit in self.coupled_qubits
        ]

        print(f"Results: {all_results}")

        all_costs = [
            np.sqrt(1 - res["tqg_fidelity_interleaved"]) ** 2 for res in all_results
        ]

        original_cz_param = cz_param
        if param_dict["cz_frequency"] is not None:
            original_cz_param["cz_pulse_frequency"] = (
                float(cz_param["cz_pulse_frequency"])
                - param_dict["cz_frequency"][self.coupler]
            )
        if param_dict["cz_duration"] is not None:
            original_cz_param["cz_pulse_duration"] = (
                float(cz_param["cz_pulse_duration"])
                - param_dict["cz_duration"][self.coupler]
            )
        if param_dict["cz_amplitude"] is not None:
            original_cz_param["cz_pulse_amplitude"] = (
                float(cz_param["cz_pulse_amplitude"])
                - param_dict["cz_amplitude"][self.coupler]
            )

        for key, value in original_cz_param.items():
            self.redis_connection.hset(f"couplers:{self.coupler}", key, value)

        # print(f"Results: {results}")
        self.all_results_list.append(
            {
                "path": str(self.data_path),
                "trial": trial.number,
                "cost": sum(all_costs),
                "param_dict": param_dict,
                "results": tqg_rb_results,
                "original_cz_parameters": original_cz_param,
                "current cz parameters:": cz_param,
            }
        )

        with open(
            self.log_path + self.time_id + "_cz_optimization_RB_all_results.py", "w"
        ) as f:
            f.write(f"all_results = {self.all_results_list}\n\n")

        print(f"Costs: {all_costs}")
        # return sum(all_costs)
        return sum(all_costs)

    def optimize_node(self):
        print(f"Optimizing {self.name} with {self.trails} trails")
        # get_current_cz_parameters_from redis

        self.study.optimize(self.objective, n_trials=self.trails)
        self.best_params = self.study.best_params
        print(
            f"Validating trail {self.study.best_trial.number} with params {self.best_params}"
        )
        self.validate()

        print(f"Optimization finished for {self.name}")
        return self.study

    def plot_optimization(self):
        fig = optuna.visualization.plot_optimization_history(self.study)
        fig.write_image(self.data_path / "optimization_history.png")
        fig.write_image(self.log_path + "optimization_history.png")
        fig.show()
        return fig

    def validate(self, name="validate"):
        param_dict = {}
        for param in self.full_params:
            if param in self.best_params:
                if param == "cz_duration":
                    values = np.array([self.best_params["cz_duration"]])
                    param_dict[param] = dict(zip(self.couplers, values))
                elif param == "cz_frequency":
                    values = np.array([self.best_params["cz_frequency"]])
                    param_dict[param] = dict(zip(self.couplers, values))
                elif param == "cz_amplitude":
                    values = np.array([self.best_params["cz_amplitude"]])
                    param_dict[param] = dict(zip(self.couplers, values))
            else:
                param_dict[param] = None

        self.validate_params = param_dict
        print(f"Validating {self.name} with {param_dict}")

        cz_param = self.redis_connection.hgetall(f"couplers:{self.coupler}")
        print("cz_param is:", cz_param)
        if param_dict["cz_frequency"] is not None:
            cz_param["cz_pulse_frequency"] = (
                float(cz_param["cz_pulse_frequency"])
                + param_dict["cz_frequency"][self.coupler] * 1e6
            )
        if param_dict["cz_duration"] is not None:
            cz_param["cz_pulse_duration"] = (
                float(cz_param["cz_pulse_duration"])
                + param_dict["cz_duration"][self.coupler] * 1e-9
            )
        if param_dict["cz_amplitude"] is not None:
            cz_param["cz_pulse_amplitude"] = (
                float(cz_param["cz_pulse_amplitude"])
                + param_dict["cz_amplitude"][self.coupler]
            )

        for key, value in cz_param.items():
            self.redis_connection.hset(f"couplers:{self.coupler}", key, value)

        node_dynamic_phase = CZDynamicPhaseSSRONode(
            "cz_dynamic_phase", self.all_qubits, self.couplers, **self.schedule_keywords
        )

        dynamic_phase = node_dynamic_phase.calibrate(
            self.data_path, self.lab_ic, self.cluster_status
        )

        node_dynamic_phase_swap = CZDynamicPhaseSwapSSRONode(
            "cz_dynamic_phase_swap", self.all_qubits, self.couplers
        )

        dynamic_phase_swap = node_dynamic_phase_swap.calibrate(
            self.data_path, self.lab_ic, self.cluster_status
        )
        # print('dynamic_pahse_results are: ', dynamic_phase_swap)

        coupler_append = "c" + self.couplers[0].replace("_", "")

        if (
            dh.get_legacy("qubit_types")[self.coupled_qubits[0]]
            == self.qubit_type_list[0]
        ):
            cz_param["cz_dynamic_target"] = (
                -1
                * dynamic_phase[self.coupled_qubits[1] + coupler_append][
                    "cz_dynamic_target"
                ]
            )
            cz_param["cz_dynamic_control"] = (
                -1
                * dynamic_phase_swap[self.coupled_qubits[0] + coupler_append][
                    "cz_dynamic_control"
                ]
            )
        else:
            cz_param["cz_dynamic_target"] = (
                -1
                * dynamic_phase[self.coupled_qubits[0] + coupler_append][
                    "cz_dynamic_target"
                ]
            )
            cz_param["cz_dynamic_control"] = (
                -1
                * dynamic_phase_swap[self.coupled_qubits[1] + coupler_append][
                    "cz_dynamic_control"
                ]
            )

        for key, value in cz_param.items():
            self.redis_connection.hset(f"couplers:{self.coupler}", key, value)

        rb_node = TQGRandomizedBenchmarkingInterleavedSSRONode(
            "tqg_randomized_benchmarking_interleaved_ssro",
            self.all_qubits,
            self.couplers,
        )

        tqg_rb_results = rb_node.calibrate(
            self.data_path, self.lab_ic, self.cluster_status
        )

        cz_node = CZCalibrationSSRONode(
            "cz_calibration_ssro", self.all_qubits, self.couplers
        )

        cz_results = cz_node.calibrate(self.data_path, self.lab_ic, self.cluster_status)

        cz_and_rb_results = tqg_rb_results | cz_results

        self.all_results_list.append(
            {
                "path": str(self.data_path),
                "trial": name,
                "param_dict": param_dict,
                "results": cz_and_rb_results,
                "cz parameters": cz_param,
            }
        )
        with open(
            self.log_path + self.time_id + "_cz_optimization_all_results.py", "w"
        ) as f:
            f.write(f"all_results = {self.all_results_list}\n\n")
        print(f"Results: {cz_and_rb_results}")
        return cz_and_rb_results

    def calibrate(self, data_path: Path, lab_ic, cluster_status):
        self.data_path = data_path
        self.lab_ic = lab_ic
        self.cluster_status = cluster_status

        if self.average:
            self.best_params = []
            for i in range(self.trails):
                self.validate(name=i)
        else:
            self.optimize_node()
            self.plot_optimization()
            with open(
                self.log_path + self.time_id + "_cz_optimization_best.py", "w"
            ) as f:
                f.write(f"best = {self.validate_params}\n\n")
                f.write(f"validate = {self.all_results_list[-1]}\n\n")

        return self.all_results_list
