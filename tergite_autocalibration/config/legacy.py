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

from typing import Dict

import toml

from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.utils.logging import logger


###
# NOTE: A global instance of DataHandler (dh) can be found below and be imported in the code
###


def update_nested(target: Dict, updates: Dict):
    """
    Update a nested data structure (usually a dict).

    Args:
        target: The original data structure
        updates: The updates that are going to be merged into the data structure

    Returns:
        Does not return anything, but works on the given objects

    """
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
    """
    A temporary class to handle the transition from the old configuration files to the
    new configuration packages
    """

    # We are using a singleton pattern, so, this holds the `DataHandler` instance
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataHandler, cls).__new__(cls)

            # TODO: Both layout and device should be fed into a Device object.
            #       Right now we are not using the device configuration.
            device_config = toml.load(CONFIG.device)
            cls._layout = device_config["layout"]

            # Iterate over the values for the device configuration to detect whether there are values
            # to be set for all qubits/couplers
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

            # This is creating a variable for the qubit type, whether it is control or target qubit
            # in a coupler
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

            # The configuration for the SPI rack
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
        """
        Temporary endpoint to provide data structures in the necessary shape as they are used in the code
        right now.

        Args:
            variable_name: Old name of the variable that has to be called
                           Can be: "VNA_resonator_frequencies", "VNA_qubit_frequencies",
                                   "VNA_f12_frequencies" for the values of the old VNA file
                                   "attenuation_setting" and "qubit_types" for the values from
                                   the old user_input.py file and "coupler_spi_mapping" to receive
                                   values in the format as it was in coupler_values.py

        Returns:

        """
        # TODO: This method is temporary and to be deprecated as soon as possible
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
            logger.warning(
                f"Cannot return data value for legacy variable: {variable_name}"
            )


# An instance of the DataHandler to be imported elsewhere in the code
dh = DataHandler()
