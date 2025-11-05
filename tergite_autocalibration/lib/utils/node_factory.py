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


from typing import Dict, List

from tergite_autocalibration.lib.base.node import Node
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
    Qubit01SpectroscopyNode,
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


class NodeFactory:
    def __init__(self):
        self.node_name_mapping: Dict[str, Node] = {
            "resonator_spectroscopy": ResonatorSpectroscopyNode,
            "qubit_01_spectroscopy": Qubit01SpectroscopyNode,
            "rabi_oscillations": RabiOscillationsNode,
            "ramsey_correction": RamseyFringesNode,
            "motzoi_parameter": MotzoiParameterNode,
            "T1": T1Node,
            "T2": T2Node,
            "T2_echo": T2EchoNode,
            "n_rabi_oscillations": NRabiOscillationsNode,
            "resonator_spectroscopy_1": ResonatorSpectroscopy1Node,
            "qubit_12_spectroscopy": Qubit12SpectroscopyMultidimNode,
            "rabi_oscillations_12": RabiOscillations12Node,
            "ramsey_correction_12": RamseyFringes12Node,
            "resonator_spectroscopy_2": ResonatorSpectroscopy2Node,
            "ro_frequency_two_state_optimization": ROFrequencyTwoStateOptimizationNode,
            "ro_amplitude_two_state_optimization": ROAmplitudeTwoStateOptimizationNode,
            "ro_frequency_three_state_optimization": ROFrequencyThreeStateOptimizationNode,
            "ro_amplitude_three_state_optimization": ROAmplitudeThreeStateOptimizationNode,
            "randomized_benchmarking": RandomizedBenchmarkingNode,
            "purity_benchmarking": PurityBenchmarkingNode,
            "coupler_anticrossing": QubitSpectroscopyVsCurrentNode,
        }

    def all_node_names(self) -> List[str]:
        return list(self.node_name_mapping.keys())

    def create_node(self, node_name: str, all_qubits: list, couplers: list, **kwargs):
        NodeObject = self.node_name_mapping[node_name]
        node_instance = NodeObject(
            node_name,
            all_qubits=all_qubits,
            couplers=couplers,
        )
        return node_instance

    def get_node_class(self, node_name: str):
        node_obj = self.node_name_mapping[node_name]
        return node_obj
