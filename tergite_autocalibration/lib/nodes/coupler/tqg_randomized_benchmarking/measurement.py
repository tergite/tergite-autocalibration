# This code is part of Tergite
#
# (C) Copyright Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np
from numpy.typing import NDArray
from quantify_scheduler import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.control_flow_library import Loop
from quantify_scheduler.operations.gate_library import Reset, X
from quantify_scheduler.operations.pulse_library import IdlePulse
from quantify_scheduler.resources import ClockResource

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.extended_coupler_edge import (
    ExtendedCompositeSquareEdge,
)
from tergite_autocalibration.utils.dto.extended_gates import (
    Measure_RO_3state_Opt,
    Rxy_12,
)
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon
from tergite_autocalibration.utils.logger.tac_logger import logger



# TODO: REMOVE THE DEPENDENCY OF THIS PACKAGE.
try:
    from superconducting_qubit_tools.clifford_module.cliffords_decomposition import (
        decompose_clifford_seq,
    )
    from superconducting_qubit_tools.clifford_module.randomized_benchmarking import (
        randomized_benchmarking_sequence,
    )
    from superconducting_qubit_tools.utils.clifford_module.from_list import (
        add_two_qubit_gates_to_schedule,
    )
except ImportError:
    logger.warning(
        "Could not find package: superconducting-qubit-tools.",
        "This is a proprietary licenced software.",
        "Please make sure that you are having a correct licence and install the dependency",
    )
    

class TQGRandomizedBenchmarkingSSRO(BaseMeasurement):
    def __init__(
        self,
        transmons: dict[str, ExtendedTransmon],
        couplers: dict[str, ExtendedCompositeSquareEdge],
        qubit_state: int = 0,
    ):
        super().__init__(transmons)
        self.transmons = transmons
        self.couplers = couplers
        self.qubit_state = qubit_state

    def schedule_function(
        self,
        seeds: int,
        number_of_cliffords: dict[str, np.ndarray],
        interleaving_clifford_id: int = None,
        apply_inverse_gate: bool = True,
        repetitions: int = 1024,
    ) -> Schedule:
        """
        Generate a schedule for performing a randomized benchmarking test using Clifford gates.
        The goal is to get a measure of the total error of the calibrated qubits.

        Schedule sequence
            Reset -> Apply Clifford operations-> Apply inverse of all Clifford operations -> Measure

        Parameters
        ----------
        repetitions
            The amount of times the Schedule will be repeated.
        **number_of_cliffords_operations
            The number of random Clifford operations applied and then inverted on each qubit state.
            This parameter is swept over.

        Returns
        -------
        :
            An experiment schedule.
        """
        if interleaving_clifford_id is None:
            name = "tqg_randomized_benchmarking_ssro"
        else:
            name = "tqg_randomized_benchmarking_interleaved_ssro"
            
        # Create a new schedule with the given name and print whether the sequence is
        # interleaved or not
        schedule = Schedule(f"{name}")
        print("interleaved or not", name)
        
        # Create a single-shot schedule to represent a basic time unit for the experiment
        shot = Schedule("shot")
        
        # Add an idle pulse of 16 nanoseconds to the shot schedule
        # This acts as a placeholder or delay to ensure timing alignment
        shot.add(IdlePulse(16e-9))

        # Initialize clock resources for each qubit in the system
        # Clock resources are used to define and manage the frequencies required for operations
        for this_qubit, this_transmon in self.transmons.items():
            
            # Get the readout frequency optimized for 3-state discrimination (|0>, |1>, |2>)
            ro_frequency = this_transmon.extended_clock_freqs.readout_3state_opt()
            
            # Add the readout clock resource to the schedule for the current qubit
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.ro_3st_opt", freq=ro_frequency)
            )
            
            # Get the qubit's f01 transition frequency (from |0> to |1>)
            mw_frequency_01 = this_transmon.clock_freqs.f01()
            
            # Add the f01 microwave clock resource to the schedule for the current qubit
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.01", freq=mw_frequency_01)
            )
            
            # Get the qubit's f12 transition frequency (from |1> to |2>)
            mw_frequency_12 = this_transmon.clock_freqs.f12()
            
            # Add the f12 microwave clock resource to the schedule for the current qubit
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.12", freq=mw_frequency_12)
            )

        qubits = list(self.transmons.keys())  # Get a list of qubit names from the transmon dict
        coupler_names = list(self.couplers.keys())  # Get a list of coupler names from the coupler dict
    
        for this_coupler_name in coupler_names:
            
            # Check if the current coupler belongs to a specific subset
            # These specific couplers have a downconversion factor of 0
            if this_coupler_name in ["q21_q22", "q22_q23", "q23_q24", "q24_q25"]:
                downconvert = 0
            else:
                # For all other couplers, use a default downconversion factor of 4.4 GHz
                downconvert = 4.4e9
            
            cz_frequency = self.couplers[this_coupler_name].clock_freqs.cz_freq()
            print("coupler frequency is", cz_frequency)
            
            clock_resource = ClockResource(name=f"{this_coupler_name}.cz", freq=(downconvert - cz_frequency))
            
            # Add a clock resource for the coupler's "CZ" (controlled-Z) gate to the schedule
            # The frequency is adjusted by subtracting the coupler's "CZ" frequency from the downconversion factor
            schedule.add_resource(clock_resource)
            
            # Similarly, add the same clock resource to the "shot" schedule
            # Ensures that the "CZ" gate is correctly configured at both levels
            shot.add_resource(clock_resource)
            
        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = shot.add(Reset(*qubits), label="Start")

        # The first for loop iterates over all qubits:
        clifford_sequence_lengths = list(number_of_cliffords.values())[0]
        num_clifford_sequence_lengths = len(clifford_sequence_lengths)
        
        # Loop over random Clifford sequence lengths, excluding the last three elements.
        # TODO: Why do we exclude the last 3 elements?!!
        for acq_index, n_cl in enumerate(clifford_sequence_lengths[:-3]):
            
            # Add an idle pulse at the start of the shot to introduce a delay
            shot.add(IdlePulse(16e-9))
            
            # TODO: THIS FUNCTION NEEDS TO BE REPLACED
            # Generate a randomized benchmarking sequence for two qubits
            clifford_seq = randomized_benchmarking_sequence(
                n_cl=n_cl,
                meas_basis_index=0,
                seed=seeds[next(iter(seeds))],
                interleaving_clifford_id=interleaving_clifford_id,
                apply_inverse_gate=apply_inverse_gate,
                number_of_qubits=2,
            )
            
            # TODO: THIS FUNCTION NEEDS TO BE REPLACED
            # Decompose the Clifford sequence into physical gate operations
            physical_gates = decompose_clifford_seq(clifford_seq, [qubits[0], qubits[1]])
            
            # Time between two-qubit gates
            separation_time = 300e-9
            
            # Add a reset operation for the qubits
            reset = shot.add(Reset(*qubits))

            # TODO: THIS FUNCTION NEEDS TO BE REPLACED
            # Add the decomposed two-qubit gates to the schedule
            add_two_qubit_gates_to_schedule(
                shot, physical_gates, ref_op=reset, separation_time=separation_time
            )

            # Add a buffer idle pulse after gate execution
            buffer = shot.add(IdlePulse(20e-9))
            
            # Perform measurement in the three-state optimized readout for each qubit
            for this_qubit in qubits:
                shot.add(
                    Measure_RO_3state_Opt(
                        this_qubit, acq_index=acq_index, bin_mode=BinMode.APPEND
                    ),
                    ref_op=buffer,
                    ref_pt="end",
                )
            
            # Add a root relaxation operation after measurements
            root_relaxation = shot.add(Reset(*qubits), label=f"Reset_tqgRB_{acq_index}")

        # Iterate over qubits to add state preparation and measurement
        for this_qubit in qubits:
            qubit_levels = range(self.qubit_state + 1)

            shot.add(Reset(*qubits), ref_op=root_relaxation, ref_pt_new="end")
            
            # To enforce parallelism we refer to the root relaxation
            # The intermediate for-loop iterates over all ro_amplitudes:
            # for ampl_indx, ro_amplitude in enumerate(ro_amplitude_values):
            # The inner for-loop iterates over all qubit levels:
            
            # Iterate over all qubit levels for state preparation and measurement
            for level_index, state_level in enumerate(qubit_levels):
                calib_index = num_clifford_sequence_lengths + level_index + 1

                # Prepare qubit states based on the state level
                if state_level == 0:
                    prep = shot.add(IdlePulse(40e-9))  # Idle pulse for ground state
                elif state_level == 1:
                    prep = shot.add(X(this_qubit))  # X gate for excited state |1>
                elif state_level == 2:
                    shot.add(X(this_qubit))  # X gate
                    prep = shot.add(Rxy_12(this_qubit))  # Rxy_12 gate for |2> state
                else:
                    raise ValueError("State Input Error")
                
                # Add measurement in three-state optimized readout mode
                shot.add(
                    Measure_RO_3state_Opt(
                        this_qubit, acq_index=calib_index, bin_mode=BinMode.APPEND
                    ),
                    ref_op=prep,
                    ref_pt="end",
                )
                
                # Add a reset operation for the qubit
                shot.add(Reset(this_qubit))

        # Add idle pulses before and after the entire shot sequence for timing alignment
        schedule.add(IdlePulse(16e-9))
        print(schedule.add(shot, control_flow=Loop(repetitions), validate=False))
        schedule.add(IdlePulse(16e-9))

        return schedule
