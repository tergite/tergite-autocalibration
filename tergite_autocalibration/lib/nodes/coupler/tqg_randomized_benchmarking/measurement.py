# This code is part of Tergite
#
# (C) Copyright Amr Osman 2024
# (C) Copyright Eleftherios Moschandreou 2025, 2026
# (C) Copyright Chalmers Next Labs 2025, 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from itertools import groupby
from operator import itemgetter
from typing import Optional

import numpy as np
from numpy.typing import NDArray
from quantify_scheduler import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.control_flow_library import LoopOperation
from quantify_scheduler.operations.gate_library import CZ, X90, Y90, Reset, Rxy, X, Y
from quantify_scheduler.operations.pulse_library import IdlePulse
from quantify_scheduler.resources import ClockResource

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.randomized_benchmarking import (
    randomized_benchmarking_sequence,
)
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.two_qubit_clifford_group import (
    TwoQubitClifford,
)
from tergite_autocalibration.utils.dto.extended_coupler_edge import (
    ExtendedCompositeSquareEdge,
)
from tergite_autocalibration.utils.dto.extended_gates import Measure_RO_3state_Opt
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon
from tergite_autocalibration.utils.logging import logger

# Constants
DOWNCONVERT_FREQ = 4.4e9
IDLE_TIME = 12e-9


class TwoQubitRBMeasurement(BaseMeasurement):

    def __init__(
        self,
        transmons: dict[str, ExtendedTransmon],
        couplers: dict[str, ExtendedCompositeSquareEdge],
    ):
        super().__init__(transmons)
        self.transmons = transmons
        self.couplers = couplers

    def allign_cliffords(self, coupler: str, clifford_sequence: list) -> list:
        def pad_operations(operation_group: dict):
            for qubit, ops in operation_group.items():
                max_len = max(len(ops) for ops in operation_group.values())
                while len(ops) < max_len:
                    ops.insert(0, "I")

        operation_group = {}
        grouped_operations = []
        for qubit, operation in groupby(clifford_sequence, key=itemgetter(1)):
            operations = [op[0] for op in operation]
            if type(qubit) is str:
                operation_group[qubit] = operations
            elif type(qubit) is list:
                if operation_group != {}:
                    pad_operations(operation_group)

                    grouped_operations.append(operation_group.copy())
                    operation_group.clear()
                operation_group[coupler] = operations
                grouped_operations.append(operation_group.copy())
                operation_group.clear()

        if operation_group != {}:
            pad_operations(operation_group)
        grouped_operations.append(operation_group.copy())
        return grouped_operations

    def add_coupler_clock_resources(self, schedule: Schedule, coupler: str) -> None:
        """
        Add a clock resource for the coupler's "CZ" (controlled-Z) gate to the schedule
        The frequency is adjusted by subtracting the coupler's "CZ" frequency from the downconversion factor

        Args:
            schedule: The schedule to add resources to
            coupler_name: Name identifier for the coupler
        """
        downconvert = DOWNCONVERT_FREQ
        cz_frequency = self.couplers[coupler].clock_freqs.cz_freq()
        clock_resource = ClockResource(
            name=f"{coupler}.cz", freq=(downconvert - cz_frequency)
        )
        schedule.add_resource(clock_resource)

    def ro_shot(
        self,
        seeds: dict[str, int],
        number_of_cliffords: dict[str, np.ndarray],
        interleave_modes: dict[str, np.ndarray],
        apply_inverse_gate: bool,
        coupler_dict: dict[str, dict],
        interleaving_clifford_id: Optional[int] = None,
    ) -> Schedule:

        shot = Schedule("shot")  # Create a single-shot schedule

        coupler_names = list(self.couplers.keys())
        this_coupler = coupler_names[0]

        control_qubit = coupler_dict[this_coupler]["control_qubit"]
        target_qubit = coupler_dict[this_coupler]["target_qubit"]

        qubit_names = [control_qubit, target_qubit]
        self.rx_duartion = self.transmons[qubit_names[0]].rxy.duration()

        print("WARNING RB SEEDING")
        seed = seeds[coupler_names[0]]

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = shot.add(Reset(*qubit_names), label="Start")

        # The first for loop iterates over all qubits:
        clifford_sequence_lengths = list(number_of_cliffords.values())[0]
        interleaves = list(interleave_modes.values())[0]
        num_clifford_sequence_lengths = len(clifford_sequence_lengths)

        # ---- PycQED mappings ----#
        pycqed_operation_map = {
            "X180": lambda q: X(q),
            "X90": lambda q: X90(q),
            "Y180": lambda q: Y(q),
            "Y90": lambda q: Y90(q),
            "I": lambda q: IdlePulse(duration=self.rx_duartion),
            "mX90": lambda q: Rxy(qubit=q, phi=0.0, theta=-90.0),
            "mY90": lambda q: Rxy(qubit=q, phi=90.0, theta=-90.0),
        }

        def add_single_qubits_operations_dict(
            schedule: Schedule, operations_dict: dict
        ):
            root = schedule.add(IdlePulse(4e-9))
            named_dict = {}
            named_dict[control_qubit] = operations_dict["q0"]
            named_dict[target_qubit] = operations_dict["q1"]
            control_qubit_operations = named_dict[control_qubit]
            for c_op in control_qubit_operations:
                gate = pycqed_operation_map[c_op](control_qubit)
                schedule.add(gate)
            schedule.add(IdlePulse(4e-9), ref_op=root)
            target_qubit_operations = named_dict[target_qubit]
            for t_op in target_qubit_operations:
                gate = pycqed_operation_map[t_op](target_qubit)
                schedule.add(gate)

        print(f"{ interleaves = }")
        for mode_index, interleave_mode in enumerate(interleaves):
            if interleave_mode:
                interleaving_clifford_id = 4368

            # Loop over random Clifford sequence lengths
            for acq_index, n_cl in enumerate(clifford_sequence_lengths):
                this_index = mode_index * num_clifford_sequence_lengths + acq_index

                # Generate a randomized benchmarking sequence for two qubits
                clifford_seq: NDArray[np.int_] = randomized_benchmarking_sequence(
                    number_of_cliffords=n_cl,
                    apply_inverse=apply_inverse_gate,
                    clifford_group=2,
                    interleaved_clifford_idx=interleaving_clifford_id,
                    seed=seed,
                )

                # Decompose Clifford sequence into physical gates
                for clifford_gate_idx in clifford_seq:
                    cl_decomp = TwoQubitClifford(clifford_gate_idx).gate_decomposition

                    # print(f"{ cl_decomp = }")
                    grouped_clifford_decomposition = self.allign_cliffords(
                        coupler_names[0], cl_decomp
                    )
                    # print(f"{ grouped_clifford_decomposition = }")

                    for group in grouped_clifford_decomposition:
                        if coupler_names[0] in group:
                            shot.add(CZ(control_qubit, target_qubit))
                        else:
                            add_single_qubits_operations_dict(shot, group)

                final = shot.add(IdlePulse(4e-9))

                shot.add(
                    Measure_RO_3state_Opt(
                        control_qubit,
                        acq_index=this_index,
                        bin_mode=BinMode.APPEND,
                    ),
                    ref_op=final,
                )
                shot.add(
                    Measure_RO_3state_Opt(
                        target_qubit,
                        acq_index=this_index,
                        bin_mode=BinMode.APPEND,
                    ),
                    ref_op=final,
                )
                shot.add(Reset(control_qubit, target_qubit))
        return shot

    def schedule_function(
        self,
        seeds: dict[str, int],
        loop_repetitions: int,
        number_of_cliffords: dict[str, np.ndarray],
        interleave_modes: dict[str, np.ndarray],
        coupler_dict: dict[str, dict],
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

        schedule = Schedule(f"{name}", repetitions=1)  # Initialize schedule

        # Initialize clock resources for each coupler in the system.
        coupler_names = list(self.couplers.keys())
        for coupler in coupler_names:
            self.add_coupler_clock_resources(schedule=schedule, coupler=coupler)

        rb_shot = self.ro_shot(
            seeds=seeds,
            number_of_cliffords=number_of_cliffords,
            interleave_modes=interleave_modes,
            interleaving_clifford_id=interleaving_clifford_id,
            apply_inverse_gate=apply_inverse_gate,
            coupler_dict=coupler_dict,
        )

        schedule.add(IdlePulse(IDLE_TIME))
        schedule.add(LoopOperation(body=rb_shot, repetitions=loop_repetitions))
        schedule.add(IdlePulse(IDLE_TIME))

        return schedule
