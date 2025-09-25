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

from typing import TYPE_CHECKING

from tergite_autocalibration.lib.nodes.characterization.purity_benchmarking.node import (
    PurityBenchmarkingNode,
)
from tergite_autocalibration.lib.nodes.characterization.randomized_benchmarking.node import (
    RandomizedBenchmarkingNode,
)
from tergite_autocalibration.lib.nodes.characterization.t1.node import T1Node
from tergite_autocalibration.lib.nodes.characterization.t2.node import (
    T2EchoNode,
    T2Node,
)
from tergite_autocalibration.lib.nodes.coupler.spectroscopy.node import (
    QubitSpectroscopyVsCurrentNode,
)
from tergite_autocalibration.lib.nodes.external_parameter_node import (
    ExternalParameterNode,
)
from tergite_autocalibration.lib.nodes.qubit_control.motzoi_parameter.node import (
    MotzoiParameterNode,
)
from tergite_autocalibration.lib.nodes.qubit_control.rabi_oscillations.node import (
    NRabiOscillationsNode,
    RabiOscillations12Node,
    RabiOscillationsNode,
)
from tergite_autocalibration.lib.nodes.qubit_control.ramsey_fringes.node import (
    RamseyFringes12Node,
    RamseyFringesNode,
)
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.node import (
    Qubit01SpectroscopyMultidimNode,
    Qubit12SpectroscopyMultidimNode,
)
from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.node import (
    ResonatorSpectroscopy1Node,
    ResonatorSpectroscopy2Node,
    ResonatorSpectroscopyNode,
)
from tergite_autocalibration.lib.nodes.readout.ro_amplitude_optimization.node import (
    ROAmplitudeThreeStateOptimizationNode,
    ROAmplitudeTwoStateOptimizationNode,
)
from tergite_autocalibration.lib.nodes.readout.ro_frequency_optimization.node import (
    ROFrequencyThreeStateOptimizationNode,
    ROFrequencyTwoStateOptimizationNode,
)
from tergite_autocalibration.lib.nodes.schedule_node import (
    OuterScheduleNode,
    ScheduleNode,
)


class NodeFactory:
    def select_node(self, node_name: str):
        match node_name:
            case "resonator_spectroscopy":
                bare_node_obj = ResonatorSpectroscopyNode
                measurement_type = ScheduleNode
            case "qubit_01_spectroscopy":
                bare_node_obj = Qubit01SpectroscopyMultidimNode
                measurement_type = ScheduleNode
            case "rabi_oscillations":
                bare_node_obj = RabiOscillationsNode
                measurement_type = ScheduleNode
            case "ramsey_correction":
                bare_node_obj = RamseyFringesNode
                measurement_type = ScheduleNode
            case "motzoi_parameter":
                bare_node_obj = MotzoiParameterNode
                measurement_type = ScheduleNode
            case "T1":
                bare_node_obj = T1Node
                measurement_type = ExternalParameterNode
            case "T2":
                bare_node_obj = T2Node
                measurement_type = ExternalParameterNode
            case "T2_echo":
                bare_node_obj = T2EchoNode
                measurement_type = ExternalParameterNode
            case "n_rabi_oscillations":
                bare_node_obj = NRabiOscillationsNode
                measurement_type = ScheduleNode
            case "resonator_spectroscopy_1":
                bare_node_obj = ResonatorSpectroscopy1Node
                measurement_type = ScheduleNode
            case "qubit_12_spectroscopy":
                bare_node_obj = Qubit12SpectroscopyMultidimNode
                measurement_type = ScheduleNode
            case "rabi_oscillations_12":
                bare_node_obj = RabiOscillations12Node
                measurement_type = ScheduleNode
            case "ramsey_correction_12":
                bare_node_obj = RamseyFringes12Node
                measurement_type = ScheduleNode
            case "resonator_spectroscopy_2":
                bare_node_obj = ResonatorSpectroscopy2Node
                measurement_type = ScheduleNode
            case "ro_frequency_two_state_optimization":
                bare_node_obj = ROFrequencyTwoStateOptimizationNode
                measurement_type = ScheduleNode
            case "ro_amplitude_two_state_optimization":
                bare_node_obj = ROAmplitudeTwoStateOptimizationNode
                measurement_type = ScheduleNode
            case "ro_frequency_three_state_optimization":
                bare_node_obj = ROFrequencyThreeStateOptimizationNode
                measurement_type = ScheduleNode
            case "ro_amplitude_three_state_optimization":
                bare_node_obj = ROAmplitudeThreeStateOptimizationNode
                measurement_type = ScheduleNode
            case "randomized_benchmarking":
                bare_node_obj = RandomizedBenchmarkingNode
                measurement_type = OuterScheduleNode
            case "purity_benchmarking":
                bare_node_obj = PurityBenchmarkingNode
                measurement_type = OuterScheduleNode
            case "coupler_anticrossing":
                bare_node_obj = QubitSpectroscopyVsCurrentNode
                measurement_type = ExternalParameterNode

        return bare_node_obj, measurement_type

    def all_node_names(self) -> list[str]:
        return [
            "resonator_spectroscopy",
            "qubit_01_spectroscopy",
            "rabi_oscillations",
            "ramsey_correction",
            "motzoi_parameter",
            "n_rabi_oscillations",
            "resonator_spectroscopy_1",
            "qubit_12_spectroscopy",
            "rabi_oscillations_12",
            "ramsey_correction_12",
            "resonator_spectroscopy_2",
            "ro_frequency_two_state_optimization",
            "ro_amplitude_two_state_optimization",
            "ro_frequency_three_state_optimization",
            "ro_amplitude_three_state_optimization",
            "coupler_anticrossing",
            "T1",
            "T2",
            "T2_echo",
        ]

    def create_node(self, node_name: str, all_qubits: list, couplers: list, **kwargs):
        NodeObject, MeasurementType = self.select_node(node_name)
        node_instance = NodeObject(
            node_name,
            all_qubits=all_qubits,
            couplers=couplers,
            measurement_type=MeasurementType(),
        )
        return node_instance

    def get_node_class(self, node_name: str):
        bare_node_obj, _ = self.select_node(node_name)
        return bare_node_obj


# class NodeFactory:
#     _instance: "NodeFactory" = None
#
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(NodeFactory, cls).__new__(cls)
#             cls.__init__(cls._instance)
#         return cls._instance
#
#     def __init__(self):
#         self.node_name_mapping: Dict[str, str] = {
#             "punchout": "PunchoutNode",
#             "resonator_spectroscopy": "ResonatorSpectroscopyNode",
#             "resonator_relaxation": "ResonatorRelaxationNode",
#             "qubit_01_spectroscopy": "Qubit01SpectroscopyMultidimNode",
#             "rabi_oscillations": "RabiOscillationsNode",
#             "ramsey_correction": "RamseyFringesNode",
#             "resonator_spectroscopy_1": "ResonatorSpectroscopy1Node",
#             "qubit_12_spectroscopy": "Qubit12SpectroscopyMultidimNode",
#             "rabi_oscillations_12": "RabiOscillations12Node",
#             "ramsey_correction_12": "RamseyFringes12Node",
#             "resonator_spectroscopy_2": "ResonatorSpectroscopy2Node",
#             "motzoi_parameter": "MotzoiParameterNode",
#             "n_rabi_oscillations": "NRabiOscillationsNode",
#             "motzoi_parameter_12": "MotzoiParameter12Node",
#             "n_rabi_oscillations_12": "NRabiOscillations12Node",
#             "qubit_spectroscopy_vs_current": "QubitSpectroscopyVsCurrentNode",
#             "resonator_spectroscopy_vs_current": "ResonatorSpectroscopyVsCurrentNode",
#             "T1": "T1Node",
#             "T2": "T2Node",
#             "T2_echo": "T2EchoNode",
#             "all_XY": "AllXYNode",
#             "reset_chevron": "ResetChevronNode",
#             "reset_calibration_ssro": "ResetCalibrationSSRONode",
#             "cz_parametrisation_fix_duration": "CZParametrizationFixDurationNode",
#             "process_tomography_ssro": "ProcessTomographySSRONode",
#             "cz_chevron": "CZChevronNode",
#             "cz_optimize_chevron": "CZOptimizeChevronNode",
#             "cz_calibration_ssro": "CZCalibrationSSRONode",
#             "cz_calibration_swap_ssro": "CZCalibrationSwapSSRONode",
#             "cz_dynamic_phase_ssro": "CZDynamicPhaseSSRONode",
#             "cz_dynamic_phase_swap_ssro": "CZDynamicPhaseSwapSSRONode",
#             "ro_frequency_two_state_optimization": "ROFrequencyTwoStateOptimizationNode",
#             "ro_frequency_three_state_optimization": "ROFrequencyThreeStateOptimizationNode",
#             "ro_amplitude_two_state_optimization": "ROAmplitudeTwoStateOptimizationNode",
#             "ro_amplitude_three_state_optimization": "ROAmplitudeThreeStateOptimizationNode",
#             "randomized_benchmarking_ssro": "RandomizedBenchmarkingSSRONode",
#             "purity_benchmarking": "PurityBenchmarkingNode",
#         }
#         self._node_implementation_paths: Dict[str, Union[str, Path]] = {}
#         self._node_classes: Dict[str, type["BaseNode"]] = {}
#
#     def all_node_names(self) -> List[str]:
#         return list(self.node_name_mapping.keys())
#
#     def get_node_class(self, node_name: str) -> type["BaseNode"]:
#         # This is to avoid importing BaseNode when calling the factory in the cli
#         global BaseNode
#         from tergite_autocalibration.lib.base.node import BaseNode
#
#         # If the node implementations are not crawled yet, search for them in the nodes module
#         if len(self._node_implementation_paths) == 0:
#             # TODO: Please not that this implementation will temporarily return also classes that do not extend BaseNode
#             #       This is less robust, but more efficient, but might cause issues e.g. when detecting node
#             #       node implementations automatically. However, for now, this does not expect to cause any problem,
#             #       because it is caught later after the import of the class below.
#             self._node_implementation_paths = find_inheriting_classes_ast_recursive(
#                 Path(__file__).parent.parent / "nodes"
#             )
#
#         # If class is unknown has never been initialized before, get it from the mapping
#         if node_name not in self._node_classes.keys():
#             cls_name = None
#             # Check whether the class is in the mapping
#             if node_name in self.node_name_mapping.keys():
#                 cls_name = self.node_name_mapping[node_name]
#             # Otherwise go through the crawled implementations
#             else:
#                 # If there is a class in the modules library that follows the camel case version of the given string,
#                 # this class can be loaded dynamically as well.
#                 for node_implementation_name in self._node_implementation_paths.keys():
#                     if camel_to_snake(node_implementation_name) == node_name:
#                         cls_name = node_implementation_name
#                         break
#             # If there is a class and module found, load it into the memory
#             if cls_name is not None:
#                 node_cls = import_class_from_file(
#                     cls_name, self._node_implementation_paths[cls_name]
#                 )
#                 if issubclass(node_cls, BaseNode):
#                     self._node_classes[node_name] = node_cls
#                 else:
#                     raise TypeError(f"Class {node_cls} does not extend BaseNode.")
#             # Otherwise raise an exception
#             else:
#                 raise NotImplementedError(
#                     f"No class implementation for node {node_name} found."
#                 )
#         return self._node_classes[node_name]
#
#     def create_node(
#         self, node_name: str, all_qubits: list[str], couplers: list[str], **kwargs
#     ) -> "BaseNode":
#         global CouplerNode, QubitNode
#         from tergite_autocalibration.lib.base.node import CouplerNode, QubitNode
#
#         # Check whether node class is already inside the dict
#         if node_name not in self._node_classes.keys():
#             node_cls = self.get_node_class(node_name)
#         else:
#             node_cls = self._node_classes[node_name]
#
#         # Create an instance of the node class
#         if issubclass(node_cls, QubitNode):
#             node_obj = node_cls(node_name, all_qubits, **kwargs)
#         elif issubclass(node_cls, CouplerNode):
#             node_obj = node_cls(node_name, couplers, **kwargs)
#         else:
#             raise TypeError(
#                 f"Node class {node_cls} is not a subclass of neither QubitNode or CouplerNode."
#             )
#
#         return node_obj
