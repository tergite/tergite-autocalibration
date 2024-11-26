# This code is part of Tergite
#
# (C) Copyright Stefan Hill 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import importlib.util
import logging
import sys
from typing import List

import toml

from .globals import CONFIG


class LegacyCalibrationConfig:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LegacyCalibrationConfig, cls).__new__(cls)

            run_config = toml.load(CONFIG.run)
            cls._target_node = run_config["general"]["target_node"]
            cls._qubits = run_config["general"]["qubits"]
            cls._couplers = run_config["general"]["couplers"]

            if CONFIG.samplespace is not None:
                us_spec_ = importlib.util.spec_from_file_location(
                    "user_samplespace", CONFIG.samplespace
                )
                user_samplespace_ = importlib.util.module_from_spec(us_spec_)
                sys.modules["user_samplespace"] = user_samplespace_
                us_spec_.loader.exec_module(user_samplespace_)
                cls._user_samplespace = user_samplespace_.user_samplespace
            else:
                cls._user_samplespace = {}

        return cls._instance

    @property
    def target_node(self) -> str:
        return self._target_node

    @property
    def qubits(self) -> List[str]:
        return self._qubits

    @property
    def couplers(self) -> List[str]:
        return self._couplers

    @property
    def user_samplespace(self):
        return self._user_samplespace


LEGACY_CONFIG = LegacyCalibrationConfig()


def update_nested(target, updates):
    for key, value in updates.items():
        if key in target:
            # If the key exists in target, check if both values are dicts
            if isinstance(value, dict) and isinstance(target[key], dict):
                # Recursively update nested dictionaries without overwriting
                update_nested(target[key], value)
            else:
                # Skip if the key exists and is not a dictionary
                continue
        else:
            # If the key does not exist in target, add it
            target[key] = value


class DataHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataHandler, cls).__new__(cls)

            device_config = toml.load(CONFIG.device)
            # FIXME: Both layout and device should be fed into a Device object
            # Right now we are not using the device configuration
            cls._layout = device_config["layout"]

            device_raw = device_config["device"]
            for device_subsection in ["resonator", "qubit", "coupler"]:
                if device_subsection in device_raw.keys():
                    global_subsection_properties = {}
                    if "all" in device_raw[device_subsection].keys():
                        global_subsection_properties = device_raw[device_subsection][
                            "all"
                        ]
                    for key_, value_ in device_raw[device_subsection].items():
                        if key_.startswith("q"):
                            update_nested(
                                device_raw[device_subsection][key_],
                                global_subsection_properties,
                            )
                    device_raw[device_subsection].pop("all")
            cls._device = device_raw

            # FIXME: Here, we are creating a temporary variable for the qubit type
            _qubit_types = {}
            for qubit in cls._device["qubit"]:
                if int(qubit[1:]) % 2 == 0:
                    # Even qubits are data/control qubits
                    qubit_type = "Control"
                else:
                    # Odd qubits are ancilla/target qubits
                    qubit_type = "Target"
                _qubit_types[qubit] = qubit_type
            cls._qubit_types = _qubit_types

            if CONFIG.cluster is not None:
                cls.cluster_config = CONFIG.cluster

            if CONFIG.spi is not None:
                cls.spi = toml.load(CONFIG.spi)

        return cls._instance

    def __init__(self):
        # We are leaving the constructor empty, since the singleton is just defined in the __new__()
        pass

    @property
    def device(self):
        return self._device

    @property
    def cluster_name(self):
        # TODO: This is under the assumption that there is only one cluster defined in the cluster config
        return str(list(self.cluster_config.hardware_description.keys())[0])

    def get_legacy(self, variable_name: str):
        # This method is temporary and to be deprecated as soon as possible
        if variable_name == "VNA_resonator_frequencies":
            return {
                i_: keys_["VNA_frequency"]
                for i_, keys_ in self._device["resonator"].items()
            }
        if variable_name == "VNA_qubit_frequencies":
            return {
                i_: keys_["VNA_f01_frequency"]
                for i_, keys_ in self._device["qubit"].items()
            }
        if variable_name == "VNA_f12_frequencies":
            return {
                i_: keys_["VNA_f12_frequency"]
                for i_, keys_ in self._device["qubit"].items()
            }
        if variable_name == "attenuation_setting":
            # TODO: attenuation setting could maybe also work with the qblox hardware configuration
            # FIXME: These are just some values, so that we do not have 0 in there
            qubit_attenuation = 10
            coupler_attenuation = 34
            resonator_attenuation = 12
            # TODO: We are now just using the first attenuation value in here,
            try:
                qubit_attenuation = list(self._device["qubit"].items())[0][1][
                    "attenuation"
                ]
            except IndexError:
                pass
            try:
                coupler_attenuation = list(self._device["coupler"].items())[0][1][
                    "attenuation"
                ]
            except IndexError:
                pass
            try:
                resonator_attenuation = list(self._device["resonator"].items())[0][1][
                    "attenuation"
                ]
            except IndexError:
                pass
            return {
                "qubit": qubit_attenuation,
                "coupler": coupler_attenuation,
                "resonator": resonator_attenuation,
            }
        elif variable_name == "qubit_types":
            return self._qubit_types
        elif variable_name == "coupler_spi_mapping":
            return self.spi["couplers"]
        else:
            logging.warning(
                f"Cannot return data value for legacy variable: {variable_name}"
            )


dh = DataHandler()
