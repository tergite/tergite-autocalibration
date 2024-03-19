from tergite_acl.lib.nodes.characterization_nodes import T1_Node, T2_Node, T2_Echo_Node, Randomized_Benchmarking_Node
from tergite_acl.lib.nodes.coupler_nodes import Coupler_Spectroscopy_Node, Coupler_Resonator_Spectroscopy_Node, \
    CZ_Chevron_Node, CZ_Optimize_Chevron_Node, Reset_Chevron_Node, CZ_Calibration_Node, CZ_Calibration_SSRO_Node, \
    CZ_Dynamic_Phase_Node
from tergite_acl.lib.nodes.qubit_control_nodes import Adaptive_Motzoi_Parameter_Node, Qubit_01_Spectroscopy_Pulsed_Node, \
    Qubit_01_Spectroscopy_Multidim_Node, Rabi_Oscillations_Node, Ramsey_Fringes_Node, Qubit_12_Spectroscopy_Pulsed_Node, \
    Qubit_12_Spectroscopy_Multidim_Node, Rabi_Oscillations_12_Node, Ramsey_Fringes_12_Node, Motzoi_Parameter_Node, \
    N_Rabi_Oscillations_Node
from tergite_acl.lib.nodes.readout_nodes import Punchout_Node, Resonator_Spectroscopy_Node, \
    Resonator_Spectroscopy_1_Node, Resonator_Spectroscopy_2_Node, RO_frequency_optimization_Node, \
    RO_frequency_optimization_gef_Node, RO_amplitude_two_state_optimization_Node, \
    RO_amplitude_three_state_optimization_Node


class NodeFactory:
    def __init__(self):
        self.node_implementations = {
            'punchout': Punchout_Node,
            'resonator_spectroscopy': Resonator_Spectroscopy_Node,
            'qubit_01_spectroscopy_pulsed': Qubit_01_Spectroscopy_Pulsed_Node,
            'qubit_01_spectroscopy': Qubit_01_Spectroscopy_Multidim_Node,
            'rabi_oscillations': Rabi_Oscillations_Node,
            'ramsey_correction': Ramsey_Fringes_Node,
            'resonator_spectroscopy_1': Resonator_Spectroscopy_1_Node,
            'qubit_12_spectroscopy_pulsed': Qubit_12_Spectroscopy_Pulsed_Node,
            'qubit_12_spectroscopy': Qubit_12_Spectroscopy_Multidim_Node,
            'rabi_oscillations_12': Rabi_Oscillations_12_Node,
            'ramsey_correction_12': Ramsey_Fringes_12_Node,
            'resonator_spectroscopy_2': Resonator_Spectroscopy_2_Node,
            'adaptive_motzoi_parameter': Adaptive_Motzoi_Parameter_Node,
            'n_rabi_oscillations': N_Rabi_Oscillations_Node,
            'coupler_spectroscopy': Coupler_Spectroscopy_Node,
            'coupler_resonator_spectroscopy': Coupler_Resonator_Spectroscopy_Node,
            'T1': T1_Node,
            'T2': T2_Node,
            'T2_echo': T2_Echo_Node,
            'reset_chevron': Reset_Chevron_Node,
            'cz_chevron': CZ_Chevron_Node,
            'cz_optimize_chevron': CZ_Optimize_Chevron_Node,
            'cz_calibration': CZ_Calibration_Node,
            'cz_calibration_ssro': CZ_Calibration_SSRO_Node,
            'cz_dynamic_phase': CZ_Dynamic_Phase_Node,
            'ro_frequency_two_state_optimization': RO_frequency_optimization_Node,
            'ro_frequency_three_state_optimization': RO_frequency_optimization_gef_Node,
            'ro_amplitude_two_state_optimization': RO_amplitude_two_state_optimization_Node,
            'ro_amplitude_three_state_optimization': RO_amplitude_three_state_optimization_Node,
            # 'ro_frequency_optimization_gef': RO_frequency_optimization_gef_Node,
            # 'state_discrimination': State_Discrimination_Node,
            'randomized_benchmarking': Randomized_Benchmarking_Node,
            # 'check_cliffords': Check_Cliffords_Node,
        }

    def all_nodes(self):
        return list(self.node_implementations.keys())

    def create_node(self, node_name: str, all_qubits: list[str], **kwargs):
        node_object = self.node_implementations[node_name](node_name, all_qubits, **kwargs)
        return node_object
