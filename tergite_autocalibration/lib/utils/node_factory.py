# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2024
# #
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import typing
from functools import cached_property
from pathlib import Path

from .reflections import find_inheriting_classes_ast_recursive, import_class_from_file
from ...utils.regex import camel_to_snake

if typing.TYPE_CHECKING:
    from ..base.node import BaseNode


class NodeFactory:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NodeFactory, cls).__new__(cls)
            cls._instance.node_name_mapping = {
                "punchout": "Punchout_Node",
                "resonator_spectroscopy": "Resonator_Spectroscopy_Node",
                "qubit_01_spectroscopy": "Qubit_01_Spectroscopy_Multidim_Node",
                "qubit_01_cw_spectroscopy": "Qubit_01_Spectroscopy_CW_Node",
                "rabi_oscillations": "Rabi_Oscillations_Node",
                "ramsey_correction": "Ramsey_Fringes_Node",
                "resonator_spectroscopy_1": "Resonator_Spectroscopy_1_Node",
                "qubit_12_spectroscopy_pulsed": "Qubit_12_Spectroscopy_Pulsed_Node",
                "qubit_12_spectroscopy": "Qubit_12_Spectroscopy_Multidim_Node",
                "rabi_oscillations_12": "Rabi_Oscillations_12_Node",
                "ramsey_correction_12": "Ramsey_Fringes_12_Node",
                "resonator_spectroscopy_2": "Resonator_Spectroscopy_2_Node",
                "motzoi_parameter": "Motzoi_Parameter_Node",
                "n_rabi_oscillations": "N_Rabi_Oscillations_Node",
                "motzoi_parameter_12": "Motzoi_Parameter_12_Node",
                "n_rabi_oscillations_12": "N_Rabi_Oscillations_12_Node",
                "coupler_spectroscopy": "Coupler_Spectroscopy_Node",
                "coupler_resonator_spectroscopy": "Coupler_Resonator_Spectroscopy_Node",
                "T1": "T1_Node",
                "T2": "T2_Node",
                "T2_echo": "T2_Echo_Node",
                "all_XY": "All_XY_Node",
                "reset_chevron": "Reset_Chevron_Node",
                "cz_characterisation_chevron": "CZ_Characterisation_Chevron_Node",
                "reset_calibration_ssro": "Reset_Calibration_SSRO_Node",
                "cz_parametrisation_fix_duration": "CZParametrisationFixDurationNode",
                "process_tomography_ssro": "Process_Tomography_Node",
                "cz_chevron": "CZ_Chevron_Node",
                "cz_optimize_chevron": "CZ_Optimize_Chevron_Node",
                "cz_calibration": "CZ_Calibration_Node",
                "cz_calibration_swap": "CZ_Calibration_Swap_Node",
                "cz_calibration_ssro": "CZ_Calibration_SSRO_Node",
                "cz_calibration_swap_ssro": "CZ_Calibration_Swap_SSRO_Node",
                "cz_dynamic_phase": "CZ_Dynamic_Phase_Node",
                "cz_dynamic_phase_swap": "CZ_Dynamic_Phase_Swap_Node",
                "ro_frequency_two_state_optimization": "RO_frequency_two_state_optimization_Node",
                "ro_frequency_three_state_optimization": "RO_frequency_three_state_optimization_Node",
                "ro_amplitude_two_state_optimization": "RO_amplitude_two_state_optimization_Node",
                "ro_amplitude_three_state_optimization": "RO_amplitude_three_state_optimization_Node",
                "randomized_benchmarking": "Randomized_Benchmarking_Node",
                "purity_benchmarking": "PurityBenchmarkingNode",
            }
            cls._node_implementation_paths = {}
            cls._node_classes = {}
        return cls._instance

    def all_node_names(self):
        return list(self.node_name_mapping.keys())

    def create_node(
        self, node_name: str, all_qubits: list[str], **kwargs
    ) -> "BaseNode":
        # If the node implementations are not crawled yet, search for them in the nodes module
        if len(self._node_implementation_paths) == 0:
            self._node_implementation_paths = find_inheriting_classes_ast_recursive(
                Path(__file__).parent.parent / "nodes"
            )

        # If class is unknown has never been initialized before, get it from the mapping
        if node_name not in self._node_classes.keys():
            cls_name = None
            # Check whether the class is in the mapping
            if node_name in self.node_name_mapping.keys():
                cls_name = self.node_name_mapping[node_name]
            # Otherwise go through the crawled implementations
            else:
                # If there is a class in the modules library that follows the camel case version of the given string,
                # this class can be loaded dynamically as well.
                for node_implementation_name in self._node_implementation_paths.keys():
                    if camel_to_snake(node_implementation_name) == node_name:
                        cls_name = node_implementation_name
                        break
            # If there is a class and module found, load it into the memory
            if cls_name is not None:
                node_cls = import_class_from_file(
                    cls_name, self._node_implementation_paths[cls_name]
                )
                self._node_classes[node_name] = node_cls
            # Otherwise raise an exception
            else:
                raise NotImplementedError(
                    f"No class implementation for node {node_name} found."
                )

        node_obj = self._node_classes[node_name](node_name, all_qubits, **kwargs)
        return node_obj
