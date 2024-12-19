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
from typing import Optional
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
    
# Constants
DEFAULT_DOWNCONVERT_FREQ = 4.4e9
SPECIAL_COUPLERS = {"q21_q22", "q22_q23", "q23_q24", "q24_q25"}
GATE_SEPARATION_TIME = 300e-9  # Time between two-qubit gates
BUFFER_TIME = 20e-9  # Buffer time after gate execution
IDLE_TIME = 16e-9
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
        
    def add_qubit_clock_resources(self, schedule: Schedule, transmon: ExtendedTransmon, qubit_name: str) -> None:
        """
        Adds three different clock resources for a given qubit to the schedule.
        The clock resources are:
            - Clock resource for readout frequency optimized for 3-state discrimination (|0>, |1>, |2>)
            - Clock resource for f01 transition frequency (from |0> to |1>)
            - Clock resource for f12 transition frequency (from |1> to |2>)
        
        Args:
            schedule: The schedule to add resources to
            transmon: The transmon qubit configuration
            qubit_name: Name identifier for the qubit
        """
        clock_resources = [
            (f"{qubit_name}.ro_3st_opt", transmon.extended_clock_freqs.readout_3state_opt()),
            (f"{qubit_name}.01", transmon.clock_freqs.f01()),
            (f"{qubit_name}.12", transmon.clock_freqs.f12())
        ]
        for name, freq in clock_resources:
            schedule.add_resource(ClockResource(name=name, freq=freq))
        
    def add_coupler_clock_resources(self, schedule: Schedule, coupler_name: str) -> None:
        """
        Add a clock resource for the coupler's "CZ" (controlled-Z) gate to the schedule
        The frequency is adjusted by subtracting the coupler's "CZ" frequency from the downconversion factor
        
        Args:
            schedule: The schedule to add resources to
            coupler_name: Name identifier for the coupler
        """
        downconvert = 0 if coupler_name in SPECIAL_COUPLERS else DEFAULT_DOWNCONVERT_FREQ
        cz_frequency = self.couplers[coupler_name].clock_freqs.cz_freq()
        clock_resource = ClockResource(
            name=f"{coupler_name}.cz",
            freq=(downconvert - cz_frequency)
        )
        schedule.add_resource(clock_resource)

        
    def prepare_state(self, shot: Schedule, qubit: str, state_level: int) -> None:
        """Prepares a qubit in a given state."""
        if state_level == 0:
            prep = shot.add(IdlePulse(40e-9))
        elif state_level == 1:
            prep = shot.add(X(qubit))
        elif state_level == 2:
            shot.add(X(qubit))
            prep = shot.add(Rxy_12(qubit))
        else:
            raise ValueError(f"Invalid state level: {state_level}")
        return prep
    
    def add_calibration_measurements(
        self,
        shot: Schedule,
        qubits: list[str],
        num_clifford_sequence_lengths: int,
        root_relaxation
    ) -> None:
        
        """Adds calibration measurements for each qubit state."""
        for qubit in qubits:
            qubit_levels = range(self.qubit_state + 1)
            shot.add(Reset(*qubits), ref_op=root_relaxation, ref_pt_new="end")
            
            for level_index, state_level in enumerate(qubit_levels):
                calib_index = num_clifford_sequence_lengths + level_index + 1
                prep = self.prepare_state(shot=shot, qubit=qubit, state_level=state_level)
                
                shot.add(
                    Measure_RO_3state_Opt(
                        qubit, 
                        acq_index=calib_index, 
                        bin_mode=BinMode.APPEND
                    ),
                    ref_op=prep,
                    ref_pt="end",
                )
                shot.add(Reset(qubit))
        

    
    def schedule_function(
        self,
        seeds: int,
        number_of_cliffords: dict[str, np.ndarray],
        interleaving_clifford_id: Optional[int] = None,
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
        # Initialize schedule
        if interleaving_clifford_id is None:
            name = "tqg_randomized_benchmarking_ssro"
        else:
            name = "tqg_randomized_benchmarking_interleaved_ssro"
        schedule = Schedule(f"{name}")
        print("interleaved or not", name)
        
        # Create a single-shot schedule to represent a basic time unit for the experiment.
        shot = Schedule("shot")
        
        # Add an idle pulse to the shot schedule.
        # This acts as a placeholder or delay to ensure timing alignment.
        shot.add(IdlePulse(IDLE_TIME))

        # Initialize clock resources for each qubit in the system.
        # Clock resources are used to define and manage the frequencies required for operations.
        for qubit_name, transmon in self.transmons.items():
            self.add_qubit_clock_resources(schedule=schedule, transmon=transmon, qubit_name=qubit_name)

        qubit_names = list(self.transmons.keys())  # Get a list of qubit names from the transmon dict.
        coupler_names = list(self.couplers.keys())  # Get a list of coupler names from the coupler dict.
        
        # Initialize clock resources for each coupler in the system.
        for coupler_name in coupler_names:
            self.add_coupler_clock_resources(schedule=schedule, coupler_name=coupler_name)
            # Similarly, add the same clock resource to the "shot" schedule
            # Ensures that the "CZ" gate is correctly configured at both levels
            self.add_coupler_clock_resources(schedule=shot, coupler_name=coupler_name)
        
        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = shot.add(Reset(*qubit_names), label="Start")

        # The first for loop iterates over all qubits:
        clifford_sequence_lengths = list(number_of_cliffords.values())[0]
        num_clifford_sequence_lengths = len(clifford_sequence_lengths)
        
        # Loop over random Clifford sequence lengths, excluding the last three elements.
        # TODO: Why do we exclude the last 3 elements?!!
        for acq_index, n_cl in enumerate(clifford_sequence_lengths[:-3]):
            # Add an idle pulse at the start of the shot to introduce a delay
            shot.add(IdlePulse(IDLE_TIME))
            
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
            physical_gates = decompose_clifford_seq(clifford_seq, [qubit_names[0], qubit_names[1]])
            
            # Add a reset operation for the qubits
            reset = shot.add(Reset(*qubit_names))

            # TODO: THIS FUNCTION NEEDS TO BE REPLACED
            # Add the decomposed two-qubit gates to the schedule
            add_two_qubit_gates_to_schedule(
                shot, physical_gates, ref_op=reset, separation_time=GATE_SEPARATION_TIME
            )

            # Add a buffer idle pulse after gate execution
            buffer = shot.add(IdlePulse(BUFFER_TIME))
            
            # Perform measurement in the three-state optimized readout for each qubit
            for qubit_name in qubit_names:
                shot.add(
                    Measure_RO_3state_Opt(
                        qubit_name, acq_index=acq_index, bin_mode=BinMode.APPEND
                    ),
                    ref_op=buffer,
                    ref_pt="end",
                )
            
            # Add a root relaxation operation after measurements
            root_relaxation = shot.add(Reset(*qubit_names), label=f"Reset_tqgRB_{acq_index}")
        
        # Add state preparation and measurement for all qubits
        self.add_calibration_measurements(shot, qubit_names, num_clifford_sequence_lengths, root_relaxation)
        
        # Finalize schedule by adding idle pulses before and after the entire shot sequence for timing alignment
        schedule.add(IdlePulse(IDLE_TIME))
        print(schedule.add(shot, control_flow=Loop(repetitions), validate=False))
        schedule.add(IdlePulse(IDLE_TIME))

        return schedule
