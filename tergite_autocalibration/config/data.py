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

import logging

import toml

from .settings import DEVICE_CONFIG


class DataHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataHandler, cls).__new__(cls)

            device_config = toml.load(DEVICE_CONFIG)
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
                            for (
                                gsp_key_,
                                gsp_value_,
                            ) in global_subsection_properties.items():
                                if (
                                    gsp_key_
                                    not in device_raw[device_subsection][key_].keys()
                                ):
                                    device_raw[device_subsection][key_][
                                        gsp_key_
                                    ] = gsp_value_
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

        return cls._instance

    def __init__(self):
        # We are leaving the constructor empty, since the singleton is just defined in the __new__()
        pass

    @property
    def device(self):
        return self._device

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
            # FIXME: These are just some values, so that we do not have 0 in there
            qubit_attenuation = 10
            coupler_attenuation = 34
            resonator_attenuation = 12
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
        else:
            logging.warning(
                f"Cannot return data value for legacy variable: {variable_name}"
            )


dh = DataHandler()
