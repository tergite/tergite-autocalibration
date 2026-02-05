# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
# (C) Copyright Michele Faucci Giannelli 2025
# (C) Copyright Axel E. Andersson 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from types import MappingProxyType

from tergite_autocalibration.config.base import TOMLConfigurationFile
from tergite_autocalibration.utils.dto.enums import QubitRole
from tergite_autocalibration.utils.logging import logger
from tergite_autocalibration.utils.misc.helpers import update_nested


class DeviceConfiguration(TOMLConfigurationFile):
    """
    Configuration for the device
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load the raw content of the device configuration file
        device_raw_ = self._dict.get("device", {})
        if not device_raw_:
            logger.warning(
                "Device configuration empty or not found, please check your device configuration."
            )
            self._obj = {}
            self._qubits = {}
            self._resonators = {}
            self._couplers = {}

        # Process the contents from the device configuration file to the full device configuration object
        else:
            for device_subsection_ in ["resonator", "qubit", "coupler"]:
                if device_subsection_ in device_raw_.keys():
                    global_subsection_properties = {}
                    if "all" in device_raw_[device_subsection_].keys():
                        global_subsection_properties = device_raw_[device_subsection_][
                            "all"
                        ]
                    for key_, value_ in device_raw_[device_subsection_].items():
                        if key_.startswith("q"):
                            update_nested(
                                device_raw_[device_subsection_][key_],
                                global_subsection_properties,
                            )
                    device_raw_[device_subsection_].pop("all")
            self._obj = device_raw_
            self._qubits = self._obj.get("qubit", {})
            self._resonators = self._obj.get("resonator", {})
            self._couplers = self._obj.get("coupler", {})

    @property
    def name(self) -> str:
        """
        Returns:
            Name of the device
        """
        return self._obj.get("name", "no_device_name_configured")

    @property
    def qubits(self) -> dict:
        """
        Returns:
            Qubit parameters as a dictionary
        """
        return self._qubits

    @property
    def resonators(self) -> dict:
        """
        Returns:
            Resonator parameters as a dictionary
        """
        return self._resonators

    @property
    def couplers(self) -> dict:
        """
        Returns:
            Coupler parameters as a dictionary
        """
        return self._couplers

    @property
    def owner(self) -> str:
        """
        Returns:
            Name of the device

        """
        return self._obj.get("owner", "no_owner_configured")

    def get_qubit_role(self, coupler_name: str, qubit_name: str) -> "QubitRole":
        """
        Get the role of a qubit in the context of a coupler for the given device.

        Args:
            coupler_name: Coupler name as str
            qubit_name: Qubit name as str

        Returns:
            Qubit role as QubitRole

        """
        qubit_role_ = QubitRole.NOTSET
        try:
            if self.couplers[coupler_name]["target_qubit"] == qubit_name:
                qubit_role_ = QubitRole.TARGET
            elif self.couplers[coupler_name]["control_qubit"] == qubit_name:
                qubit_role_ = QubitRole.CONTROL
        finally:
            return qubit_role_

    def get_output_attenuations(
        self,
    ) -> MappingProxyType[str, MappingProxyType[str, int]]:
        """
        This is an intentional bypass of the hardware config method of setting the attenuation.
        This is because for higher energy levels you almost always want the same attenuation,
        but Quantify scheduler requires the clocks to be different (since frequency of transition is statefully stored
        in the clock resource). This causes a lot of repetition in the cluster config.

        NOTE: In QCM-RF, maximum output attenuation is 60 dB (see: https://docs.qblox.com/en/main/cluster/qcm_rf.html#variable-attenuator)
        NOTE: In QCM-RF-II, maximum output attenuation is 30 dB (see: https://docs.qblox.com/en/main/cluster/qcm_rf.html#variable-attenuator)
        NOTE: In QRM-RF, maximum output attenuation is 60 dB (see: https://docs.qblox.com/en/main/cluster/qrm_rf.html#variable-attenuator)
        """
        xy = MappingProxyType(
            {
                qubit_name: data.get("attenuation", 30)
                for qubit_name, data in self.qubits.items()
            }
        )
        z = MappingProxyType(
            {
                qubit_name: data.get("attenuation", 30)
                for qubit_name, data in self.couplers.items()
            }
        )
        ro = MappingProxyType(
            {
                qubit_name: data.get("attenuation", 60)
                for qubit_name, data in self.resonators.items()
            }
        )

        return MappingProxyType({"resonator": ro, "coupler": z, "qubit": xy})
