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


class NodeFactory:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            from tergite_autocalibration.lib.nodes.characterization.t2.node import (
                T2_Node,
                T2_Echo_Node,
            )
            from tergite_autocalibration.lib.nodes.characterization.t1.node import (
                T1_Node,
            )
            from tergite_autocalibration.lib.nodes.characterization.randomized_benchmarking.node import (
                Randomized_Benchmarking_Node,
            )
            from tergite_autocalibration.lib.nodes.characterization.purity_benchmarking.node import (
                PurityBenchmarkingNode,
            )
            from tergite_autocalibration.lib.nodes.characterization.all_xy.node import (
                All_XY_Node,
            )
            from tergite_autocalibration.lib.nodes.coupler.cz_dynamic_phase.node import (
                CZ_Dynamic_Phase_Node,
                CZ_Dynamic_Phase_Swap_Node,
            )
            from tergite_autocalibration.lib.nodes.coupler.cz_calibration.node import (
                CZ_Calibration_Node,
                CZ_Calibration_SSRO_Node,
                CZ_Calibration_Swap_Node,
                CZ_Calibration_Swap_SSRO_Node,
                Reset_Calibration_SSRO_Node,
            )
            from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.node import (
                CZParametrisationFixDurationNode,
            )
            # from tergite_autocalibration.lib.nodes.coupler.cz_chevron.node import (
            #     CZ_Chevron_Node,
            #     CZ_Characterisation_Chevron_Node,
            #     CZ_Optimize_Chevron_Node,
            # )
            from tergite_autocalibration.lib.nodes.coupler.reset_chevron.node import (
                Reset_Chevron_Node,
            )
            from tergite_autocalibration.lib.nodes.coupler.process_tomography.node import (
                Process_Tomography_Node,
            )
            from tergite_autocalibration.lib.nodes.coupler.spectroscopy.node import (
                Coupler_Spectroscopy_Node,
                Coupler_Resonator_Spectroscopy_Node,
            )
            from tergite_autocalibration.lib.nodes.qubit_control.ramsey_fringes.node import (
                Ramsey_Fringes_12_Node,
                Ramsey_Fringes_Node,
            )
            from tergite_autocalibration.lib.nodes.qubit_control.rabi_oscillations.node import (
                Rabi_Oscillations_Node,
                N_Rabi_Oscillations_Node,
                Rabi_Oscillations_12_Node,
                N_Rabi_Oscillations_12_Node,
            )
            from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.node import (
                Qubit_01_Spectroscopy_Multidim_Node,
                Qubit_12_Spectroscopy_Pulsed_Node,
                Qubit_12_Spectroscopy_Multidim_Node,
            )
            from tergite_autocalibration.lib.nodes.qubit_control.motzoi_parameter.node import (
                Motzoi_Parameter_Node,
                Motzoi_Parameter_12_Node,
            )
            from tergite_autocalibration.lib.nodes.readout.ro_amplitude_optimization.node import (
                RO_amplitude_two_state_optimization_Node,
                RO_amplitude_three_state_optimization_Node,
            )
            from tergite_autocalibration.lib.nodes.readout.ro_frequency_optimization.node import (
                RO_frequency_two_state_optimization_Node,
                RO_frequency_three_state_optimization_Node,
            )
            from tergite_autocalibration.lib.nodes.readout.punchout.node import (
                Punchout_Node,
            )
            from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.node import (
                Resonator_Spectroscopy_Node,
                Resonator_Spectroscopy_1_Node,
                Resonator_Spectroscopy_2_Node,
            )

            cls._instance = super(NodeFactory, cls).__new__(cls)
            cls._instance.node_implementations = {
                "punchout": Punchout_Node,
                "resonator_spectroscopy": Resonator_Spectroscopy_Node,
                "qubit_01_spectroscopy": Qubit_01_Spectroscopy_Multidim_Node,
                "rabi_oscillations": Rabi_Oscillations_Node,
                "ramsey_correction": Ramsey_Fringes_Node,
                "resonator_spectroscopy_1": Resonator_Spectroscopy_1_Node,
                "qubit_12_spectroscopy_pulsed": Qubit_12_Spectroscopy_Pulsed_Node,
                "qubit_12_spectroscopy": Qubit_12_Spectroscopy_Multidim_Node,
                "rabi_oscillations_12": Rabi_Oscillations_12_Node,
                "ramsey_correction_12": Ramsey_Fringes_12_Node,
                "resonator_spectroscopy_2": Resonator_Spectroscopy_2_Node,
                "motzoi_parameter": Motzoi_Parameter_Node,
                "n_rabi_oscillations": N_Rabi_Oscillations_Node,
                "motzoi_parameter_12": Motzoi_Parameter_12_Node,
                "n_rabi_oscillations_12": N_Rabi_Oscillations_12_Node,
                "coupler_spectroscopy": Coupler_Spectroscopy_Node,
                "coupler_resonator_spectroscopy": Coupler_Resonator_Spectroscopy_Node,
                "T1": T1_Node,
                "T2": T2_Node,
                "T2_echo": T2_Echo_Node,
                "all_XY": All_XY_Node,
                "reset_chevron": Reset_Chevron_Node,
                "reset_calibration_ssro": Reset_Calibration_SSRO_Node,
                "cz_parametrisation_fix_duration": CZParametrisationFixDurationNode,
                "process_tomography_ssro": Process_Tomography_Node,
                # "cz_characterisation_chevron": CZ_Characterisation_Chevron_Node,
                # "cz_chevron": CZ_Chevron_Node,
                # "cz_optimize_chevron": CZ_Optimize_Chevron_Node,
                "cz_calibration": CZ_Calibration_Node,
                "cz_calibration_swap": CZ_Calibration_Swap_Node,
                "cz_calibration_ssro": CZ_Calibration_SSRO_Node,
                "cz_calibration_swap_ssro": CZ_Calibration_Swap_SSRO_Node,
                "cz_dynamic_phase": CZ_Dynamic_Phase_Node,
                "cz_dynamic_phase_swap": CZ_Dynamic_Phase_Swap_Node,
                "ro_frequency_two_state_optimization": RO_frequency_two_state_optimization_Node,
                "ro_frequency_three_state_optimization": RO_frequency_three_state_optimization_Node,
                "ro_amplitude_two_state_optimization": RO_amplitude_two_state_optimization_Node,
                "ro_amplitude_three_state_optimization": RO_amplitude_three_state_optimization_Node,
                "randomized_benchmarking": Randomized_Benchmarking_Node,
                "purity_benchmarking": PurityBenchmarkingNode,
            }
        return cls._instance

    def all_nodes(self):
        return list(self.node_implementations.keys())

    def create_node(self, node_name: str, all_qubits: list[str], **kwargs):
        node_object = self.node_implementations[node_name](
            node_name, all_qubits, **kwargs
        )
        return node_object
