# This code is part of Tergite
#
# (C) Copyright Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024
# (C) Copyright Chalmers Next Labs 2025
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
from quantify_scheduler.operations.gate_library import (
    Reset,
    CZ,
    X90,
    Y90,
    Measure,
    Reset,
    Rxy,
    X,
    Y,
)
from quantify_scheduler.operations.pulse_library import IdlePulse
from quantify_scheduler.resources import ClockResource
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.two_qubit_clifford_group import (
    TwoQubitClifford,
)

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.extended_coupler_edge import (
    ExtendedCompositeSquareEdge,
)
from tergite_autocalibration.utils.dto.extended_gates import (
    Measure_RO_3state_Opt,
    Rxy_12,
)
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon
from tergite_autocalibration.utils.logging import logger
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.randomized_benchmarking import (
    randomized_benchmarking_sequence,
)


# Constants
DEFAULT_DOWNCONVERT_FREQ = 4.4e9
SPECIAL_COUPLERS = {"q21_q22", "q22_q23", "q23_q24", "q24_q25"}
GATE_SEPARATION_TIME = 300e-9  # Time between two-qubit gates
BUFFER_TIME = 20e-9  # Buffer time after gate execution
IDLE_TIME = 16e-9


class TQGRandomizedBenchmarkingSSROMeasurement(BaseMeasurement):

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

    def add_qubit_clock_resources(
        self, schedule: Schedule, transmon: ExtendedTransmon, qubit_name: str
    ) -> None:
        """
        Adds three clock resources for a given qubit to the schedule.
        The three clock resources are:
            - Clock resource for readout frequency optimized for 3-state discrimination (|0>, |1>, |2>)
            - Clock resource for f01 transition frequency (from |0> to |1>)
            - Clock resource for f12 transition frequency (from |1> to |2>)

        Args:
            schedule: The schedule to add resources to
            transmon: The transmon qubit configuration
            qubit_name: Name identifier for the qubit
        """
        clock_resources = [
            (
                f"{qubit_name}.ro_3st_opt",
                transmon.extended_clock_freqs.readout_3state_opt(),
            ),
            (f"{qubit_name}.01", transmon.clock_freqs.f01()),
            (f"{qubit_name}.12", transmon.clock_freqs.f12()),
        ]
        for name, freq in clock_resources:
            schedule.add_resource(ClockResource(name=name, freq=freq))

    def add_coupler_clock_resources(
        self, schedule: Schedule, coupler_name: str
    ) -> None:
        """
        Add a clock resource for the coupler's "CZ" (controlled-Z) gate to the schedule
        The frequency is adjusted by subtracting the coupler's "CZ" frequency from the downconversion factor

        Args:
            schedule: The schedule to add resources to
            coupler_name: Name identifier for the coupler
        """
        downconvert = (
            0 if coupler_name in SPECIAL_COUPLERS else DEFAULT_DOWNCONVERT_FREQ
        )
        cz_frequency = self.couplers[coupler_name].clock_freqs.cz_freq()
        clock_resource = ClockResource(
            name=f"{coupler_name}.cz", freq=(downconvert - cz_frequency)
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
        root_relaxation,
    ) -> None:
        """Adds calibration measurements for each qubit state."""
        for qubit in qubits:
            qubit_levels = range(self.qubit_state + 1)
            shot.add(Reset(*qubits), ref_op=root_relaxation, ref_pt_new="end")

            for level_index, state_level in enumerate(qubit_levels):
                calib_index = num_clifford_sequence_lengths + level_index + 1
                prep = self.prepare_state(
                    shot=shot, qubit=qubit, state_level=state_level
                )

                shot.add(
                    Measure_RO_3state_Opt(
                        qubit, acq_index=calib_index, bin_mode=BinMode.APPEND
                    ),
                    ref_op=prep,
                    ref_pt="end",
                )
                shot.add(Reset(qubit))

    def schedule_function(
        self,
        seed: int,
        loop_repetitions: int,
        number_of_cliffords: dict[str, np.ndarray],
        interleaving_clifford_id: Optional[int] = None,
        apply_inverse_gate: bool = True,
    ) -> Schedule:
        """
        Generates a schedule for performing randomized benchmarking (RB) experiments using Clifford gates
        to measure qubit error rates. The schedule creates a sequence of operations including state
        preparation, random Clifford operations, inverse operations, and measurement.

        The basic sequence for each shot is:
            1. Reset qubits to ground state
            2. Apply random sequence of Clifford operations
            3. Apply inverse Clifford operations (optional)
            4. Measure qubit states
            5. Reset for next iteration

        Parameters
        ----------
        seed : int
            Random seed for generating Clifford sequences, ensuring reproducibility.
        loop_repetitions : int
            Number of times to repeat the entire schedule for statistical averaging.
        number_of_cliffords : dict[str, np.ndarray]
            Dictionary mapping qubit names to arrays of Clifford operation counts.
            Each array specifies the number of random Clifford operations to apply
            in different experimental sequences.
        interleaving_clifford_id : Optional[int], default=None
            If provided, specifies the ID of a Clifford gate to interleave between
            random Clifford operations. Used for interleaved RB experiments to
            characterize specific gate fidelities.
        apply_inverse_gate : bool, default=True
            Whether to apply inverse Clifford operations after the random sequence.
            The inverse operations should return the qubits to their initial state
            in the absence of errors.

        Returns
        -------
        Schedule
            A complete experimental schedule containing all pulses, measurements,
            and control flow for the RB experiment.

        Notes
        -----
        - The schedule includes proper clock resource initialization for both qubits
        and couplers to ensure correct timing and frequency control.
        - Measurements use three-state optimized readout for improved fidelity.
        - The schedule includes buffer times and idle pulses to ensure proper timing
        alignment between operations.
        - The last three elements of the Clifford sequence lengths are currently
        excluded (marked as TODO for investigation).
        """

        if interleaving_clifford_id is None:
            name = "tqg_randomized_benchmarking_ssro"
        else:
            name = "tqg_randomized_benchmarking_interleaved_ssro"
        logger.info(f"interleaved or not: {name}")

        schedule = Schedule(f"{name}")  # Initialize schedule
        shot = Schedule("shot")  # Create a single-shot schedule
        shot.add(IdlePulse(IDLE_TIME))  # Add an idle pulse to the shot schedule.

        # Initialize clock resources for each qubit in the system.
        for qubit_name, transmon in self.transmons.items():
            self.add_qubit_clock_resources(
                schedule=schedule, transmon=transmon, qubit_name=qubit_name
            )

        qubit_names = list(self.transmons.keys())
        coupler_names = list(self.couplers.keys())

        # Initialize clock resources for each coupler in the system.
        for coupler_name in coupler_names:
            self.add_coupler_clock_resources(
                schedule=schedule, coupler_name=coupler_name
            )
            # Similarly, add the same clock resource to the "shot" schedule
            self.add_coupler_clock_resources(schedule=shot, coupler_name=coupler_name)

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = shot.add(Reset(*qubit_names), label="Start")

        # The first for loop iterates over all qubits:
        clifford_sequence_lengths = list(number_of_cliffords.values())[0]
        num_clifford_sequence_lengths = len(clifford_sequence_lengths)

        # ---- PycQED mappings ----#
        pycqed_qubit_map = {f"q{idx}": name for idx, name in enumerate(qubit_names)}
        pycqed_operation_map = {
            "X180": lambda q: X(pycqed_qubit_map[q]),
            "X90": lambda q: X90(pycqed_qubit_map[q]),
            "Y180": lambda q: Y(pycqed_qubit_map[q]),
            "Y90": lambda q: Y90(pycqed_qubit_map[q]),
            "mX90": lambda q: Rxy(qubit=pycqed_qubit_map[q], phi=0.0, theta=-90.0),
            "mY90": lambda q: Rxy(qubit=pycqed_qubit_map[q], phi=90.0, theta=-90.0),
            "CZ": lambda q: CZ(qC=pycqed_qubit_map[q[0]], qT=pycqed_qubit_map[q[1]]),
        }

        # Loop over random Clifford sequence lengths, excluding the last three elements.
        # TODO: Why do we exclude the last 3 elements?!!
        for acq_index, n_cl in enumerate(clifford_sequence_lengths[:-3]):
            shot.add(IdlePulse(IDLE_TIME))  # start

            # Generate a randomized benchmarking sequence for two qubits
            clifford_seq: NDArray[np.int_] = randomized_benchmarking_sequence(
                n_cl=n_cl,
                apply_inverse_gate=apply_inverse_gate,
                number_of_qubits=2,
                interleaving_clifford_id=interleaving_clifford_id,
                seed=seed,
            )

            shot.add(Reset(*qubit_names))  # reset

            # Decompose Clifford sequence into physical gates
            for clifford_gate_idx in clifford_seq:
                cl_decomp = TwoQubitClifford(clifford_gate_idx).gate_decomposition

                operations = [
                    pycqed_operation_map[gate](q)
                    for (gate, q) in cl_decomp
                    if gate != "I"
                ]
                for op in operations:
                    shot.add(op, rel_time=BUFFER_TIME)

            buffer = shot.add(IdlePulse(BUFFER_TIME))
            # Perform measurement
            for qubit_name in qubit_names:
                shot.add(
                    Measure_RO_3state_Opt(
                        qubit_name, acq_index=acq_index, bin_mode=BinMode.APPEND
                    ),
                    ref_op=buffer,
                    ref_pt="end",
                )
            # Add a root relaxation operation after measurements
            root_relaxation = shot.add(
                Reset(*qubit_names), label=f"Reset_tqgRB_{acq_index}"
            )

        # Add state preparation and measurement for all qubits
        self.add_calibration_measurements(
            shot, qubit_names, num_clifford_sequence_lengths, root_relaxation
        )

        schedule.add(IdlePulse(IDLE_TIME))
        logger.info(schedule.add(shot, control_flow=Loop(loop_repetitions)))
        schedule.add(IdlePulse(IDLE_TIME))

        return schedule
