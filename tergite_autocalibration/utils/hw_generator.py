# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# TODO: This whole file would have to be reworked


class HW_Config_Generator:
    def __init__(
        self,
        cluster_name: str,
        module_to_ro_line_qubit_map: dict,
        qcm_module_to_qubit_map: dict,
        mixer_calibrations: dict = {},
    ):
        self.cluster_name = cluster_name
        self.hardware_config = self.generate_initial_hw_config()
        self.module_to_ro_line_qubit_map = module_to_ro_line_qubit_map
        self.qcm_module_to_qubit_map = qcm_module_to_qubit_map
        self.mixer_calibrations = mixer_calibrations

    def generate_initial_hw_config(self):
        HW_CONFIG = {}
        HW_CONFIG["backend"] = (
            "quantify_scheduler.backends.qblox_backend.hardware_compile"
        )
        HW_CONFIG[f"{self.cluster_name}"] = {
            "ref": "internal",
            "instrument_type": "Cluster",
        }
        return HW_CONFIG

    def generate_QRM_config(self):
        QRM_config = {}
        for module, qrm_qubits in self.module_to_ro_line_qubit_map.items():
            qrm_module_config = self.mixer_calibrations[module]
            qrm_config = self.qrm_hw(qrm_qubits, **qrm_module_config)
            QRM_config[f"{self.cluster_name}_{module}"] = qrm_config
        return QRM_config

    def generate_QCM_config(self):
        QCM_config = {}
        for module, qcm_qubit in self.qcm_module_to_qubit_map.items():
            qcm_module_config = self.mixer_calibrations[module]
            qcm_config = self.qcm_hw(qubit=qcm_qubit, **qcm_module_config)
            QCM_config[f"{self.cluster_name}_{module}"] = qcm_config
        return QCM_config

    def qrm_hw(
        self,
        qubits,
        lo_freq=6e9,
        off_I=0.0,
        off_Q=0.0,
        amp_ratio=1.0,
        phase=0.0,
    ):
        ro = []  # readout when qubit at |0>
        ro1 = []  # readout when qubit at |1>
        ro2 = []  # readout when qubit at |2>
        ro_2st_opt = []  # readout for optimum 2 state discrimination
        ro_3st_opt = []  # readout for optimum 3 state discrimination

        def standard_ro_config(ro_clock: str) -> dict:
            ro_config = {
                "port": f"{qubit}:res",
                "clock": f"{qubit}.{ro_clock}",
                "mixer_amp_ratio": amp_ratio,
                "mixer_phase_error_deg": phase,
            }
            return ro_config

        for qubit in qubits:
            ro_config = standard_ro_config("ro")
            ro.append(ro_config)

            ro1_config = standard_ro_config("ro1")
            ro1.append(ro1_config)

            ro2_config = standard_ro_config("ro2")
            ro2.append(ro2_config)

            ro_2st_opt_config = standard_ro_config("ro_2st_opt")
            ro_2st_opt.append(ro_2st_opt_config)

            ro_3st_opt_config = standard_ro_config("ro_3st_opt")
            ro_3st_opt.append(ro_3st_opt_config)

        hw = {
            "instrument_type": "QRM_RF",
            "complex_output_0": {
                "lo_freq": lo_freq,
                "dc_mixer_offset_I": off_I * 1e-3,
                "dc_mixer_offset_Q": off_Q * 1e-3,
                "portclock_configs": ro + ro1 + ro2 + ro_2st_opt + ro_3st_opt,
            },
        }
        return hw

    def qcm_hw(
        self,
        qubit,
        lo_freq=4e9,
        off_I=0.0,
        off_Q=0.0,
        amp_ratio=1.0,
        phase=0.0,
        amp_ratio_2=1.0,
        phase_2=0.0,
    ):
        hw = {
            "instrument_type": "QCM_RF",
            "complex_output_0": {
                "lo_freq": lo_freq,
                "dc_mixer_offset_I": off_I * 1e-3,
                "dc_mixer_offset_Q": off_Q * 1e-3,
                "portclock_configs": [
                    {
                        "port": f"{qubit}:mw",
                        "clock": f"{qubit}.01",
                        "mixer_amp_ratio": amp_ratio,
                        "mixer_phase_error_deg": phase,
                    },
                    {
                        "port": f"{qubit}:mw",
                        "clock": f"{qubit}.12",
                        "mixer_amp_ratio": amp_ratio_2,
                        "mixer_phase_error_deg": phase_2,
                    },
                ],
            },
        }
        return hw

    def hardware_configuration(self):
        self.hardware_config[f"{self.cluster_name}"].update(self.generate_QCM_config())
        self.hardware_config[f"{self.cluster_name}"].update(self.generate_QRM_config())
        return self.hardware_config


if __name__ == "main":
    from tergite_autocalibration.config.globals import ENV

    mixer_file = ENV.config_dir / "initial.csv"
    json_config_file = ENV.config_dir / "HARDWARE_CONFIGURATION_LOKIA_20240504.json"
    CLUSTER_NAME = "clusterA"
    HW_CONFIG = {}
    HW_CONFIG["backend"] = "quantify_scheduler.backends.qblox_backend.hardware_compile"
    HW_CONFIG[f"{CLUSTER_NAME}"] = {
        "ref": "internal",
        "instrument_type": "Cluster",
    }

    module_to_qubit_map = {
        "module1": "q06",
        "module2": "q07",
        "module3": "q08",
        "module4": "q09",
        "module5": "q10",
        "module6": "q11",
        "module7": "q12",
        "module8": "q13",
        "module9": "q14",
        "module10": "q15",
    }
    module_to_ro_line_qubit_map = {
        "module16": ["q06", "q07", "q08", "q09", "q10"],
        "module17": ["q11", "q12", "q13", "q14", "q15"],
    }
    qrm_modules = list(module_to_ro_line_qubit_map.keys())

    qubits = module_to_qubit_map.values()
