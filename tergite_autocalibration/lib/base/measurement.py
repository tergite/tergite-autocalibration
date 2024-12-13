# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Stefan Hill 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from quantify_scheduler.enums import BinMode


class BaseMeasurement:
    def __init__(self, transmons: dict, couplers: dict = {}):
        self.transmons = transmons
        self.couplers = couplers
        self.qubits = list(self.transmons.keys())
        self.device_configuration = {}
        self.bin_mode = BinMode.AVERAGE

        # def attributes_dictionary(self, parameter):
        #     """
        # TODO does this actually do anything?
        #     Create a dictionary, with qubits as keys and parameters as values.
        #     The values are actual values str or float, not qcodes references.
        #     """
        #     attr_dict = {}
        #
        #     for transmon in self.transmons.values():
        #         qubit = transmon.name
        #         if parameter == 'readout_port':
        #             attr_dict[qubit] = transmon.ports.readout()
        #         elif parameter == 'artificial_detuning':
        #             redis_key = f'transmons:{qubit}'
        #             attr_dict[qubit] = float(REDIS_CONNECTION.hget(f"{redis_key}", parameter))
        #         else:
        #             for submodule in transmon.submodules.values():
        #                 if parameter in submodule.parameters:
        #                     attr_dict[qubit] = submodule.parameters[parameter]()

        # if len(self.couplers) > 0:
        #     for coupler in self.couplers.values():
        #         bus = coupler.name
        #         for submodule in coupler.submodules.values():
        #             if parameter in submodule.parameters:
        #                 attr_dict[bus] = submodule.parameters[parameter]()
        # return attr_dict

    def set_bin_mode(self, bin_mode: str):
        bin_mode = getattr(BinMode, bin_mode, None)
        if bin_mode is not None:
            self.bin_mode = bin_mode
        else:
            raise ValueError(f"bin mode {bin_mode} isn't defined in Quantify now.")
