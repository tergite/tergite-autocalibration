# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2024
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from pathlib import Path
from typing import Dict, List, Union, TYPE_CHECKING

from .reflections import find_inheriting_classes_ast_recursive, import_class_from_file
from tergite_autocalibration.utils.misc.regex import camel_to_snake

if TYPE_CHECKING:
    from ..base.node import BaseNode


class NodeFactory:
    _instance: "NodeFactory" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NodeFactory, cls).__new__(cls)
            cls.__init__(cls._instance)
        return cls._instance

    def __init__(self):
        self.node_name_mapping: Dict[str, str] = {
            "punchout": "PunchoutNode",
            "resonator_spectroscopy": "ResonatorSpectroscopyNode",
            "resonator_relaxation": "ResonatorRelaxationNode",
            "qubit_01_spectroscopy": "Qubit01SpectroscopyMultidimNode",
            "rabi_oscillations": "RabiOscillationsNode",
            "ramsey_correction": "RamseyFringesNode",
            "resonator_spectroscopy_1": "ResonatorSpectroscopy1Node",
            "qubit_12_spectroscopy_pulsed": "Qubit12SpectroscopyPulsedNode",
            "qubit_12_spectroscopy": "Qubit12SpectroscopyMultidimNode",
            "rabi_oscillations_12": "RabiOscillations12Node",
            "ramsey_correction_12": "RamseyFringes12Node",
            "resonator_spectroscopy_2": "ResonatorSpectroscopy2Node",
            "motzoi_parameter": "MotzoiParameterNode",
            "n_rabi_oscillations": "NRabiOscillationsNode",
            "motzoi_parameter_12": "MotzoiParameter12Node",
            "n_rabi_oscillations_12": "NRabiOscillations12Node",
            "coupler_spectroscopy": "CouplerSpectroscopyNode",
            "coupler_resonator_spectroscopy": "CouplerResonatorSpectroscopyNode",
            "T1": "T1Node",
            "T2": "T2Node",
            "T2_echo": "T2EchoNode",
            "all_XY": "AllXYNode",
            "reset_chevron": "ResetChevronNode",
            "cz_characterisation_chevron": "CZCharacterisationChevronNode",
            "reset_calibration_ssro": "ResetCalibrationSSRONode",
            "cz_parametrisation_fix_duration": "CZParametrizationFixDurationNode",
            "process_tomography_ssro": "ProcessTomographySSRONode",
            "cz_chevron": "CZChevronNode",
            "cz_optimize_chevron": "CZOptimizeChevronNode",
            "cz_calibration_ssro": "CZCalibrationSSRONode",
            "cz_calibration_swap_ssro": "CZCalibrationSwapSSRONode",
            "cz_dynamic_phase_ssro": "CZDynamicPhaseSSRONode",
            "cz_dynamic_phase_swap_ssro": "CZDynamicPhaseSwapSSRONode",
            "ro_frequency_two_state_optimization": "ROFrequencyTwoStateOptimizationNode",
            "ro_frequency_three_state_optimization": "ROFrequencyThreeStateOptimizationNode",
            "ro_amplitude_two_state_optimization": "ROAmplitudeTwoStateOptimizationNode",
            "ro_amplitude_three_state_optimization": "ROAmplitudeThreeStateOptimizationNode",
            "randomized_benchmarking_ssro": "RandomizedBenchmarkingSSRONode",
            "tqg_randomized_benchmarking_ssro": "TQGRandomizedBenchmarkingSSRONode",
            "tqg_randomized_benchmarking_interleaved_ssro": "TQGRandomizedBenchmarkingInterleavedSSRONode",
            "purity_benchmarking": "PurityBenchmarkingNode",
            "cz_rb_optimize_ssro": "CZRBOptimizeSSRONode",
        }
        self._node_implementation_paths: Dict[str, Union[str, Path]] = {}
        self._node_classes: Dict[str, type["BaseNode"]] = {}

    def all_node_names(self) -> List[str]:
        return list(self.node_name_mapping.keys())

    def get_node_class(self, node_name: str) -> type["BaseNode"]:
        # This is to avoid importing BaseNode when calling the factory in the cli
        global BaseNode
        from ..base.node import BaseNode

        # If the node implementations are not crawled yet, search for them in the nodes module
        if len(self._node_implementation_paths) == 0:
            # TODO: Please not that this implementation will temporarily return also classes that do not extend BaseNode
            #       This is less robust, but more efficient, but might cause issues e.g. when detecting node
            #       node implementations automatically. However, for now, this does not expect to cause any problem,
            #       because it is caught later after the import of the class below.
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
                if issubclass(node_cls, BaseNode):
                    self._node_classes[node_name] = node_cls
                else:
                    raise TypeError(f"Class {node_cls} does not extend BaseNode.")
            # Otherwise raise an exception
            else:
                raise NotImplementedError(
                    f"No class implementation for node {node_name} found."
                )
        return self._node_classes[node_name]

    def create_node(
        self, node_name: str, all_qubits: list[str], **kwargs
    ) -> "BaseNode":
        # Check whether node class is already inside the dict
        if node_name not in self._node_classes.keys():
            node_cls = self.get_node_class(node_name)
        else:
            node_cls = self._node_classes[node_name]

        # Create an instance of the node class
        node_obj = node_cls(node_name, all_qubits, **kwargs)
        return node_obj
