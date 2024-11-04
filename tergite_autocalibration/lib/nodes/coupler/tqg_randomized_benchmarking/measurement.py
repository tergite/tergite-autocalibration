# This code is part of Tergite
#
# (C) Copyright Amr Osman 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Reset, Measure, X
from quantify_scheduler.operations.pulse_library import IdlePulse
from quantify_scheduler.resources import ClockResource

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.extended_coupler_edge import CompositeSquareEdge
from tergite_autocalibration.utils.dto.extended_gates import Rxy_12
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon
from tergite_autocalibration.utils.logger.tac_logger import logger

try:
    from superconducting_qubit_tools.clifford_module.randomized_benchmarking import *
    from superconducting_qubit_tools.clifford_module.cliffords_decomposition import (
        decompose_clifford_seq,
    )
    from superconducting_qubit_tools.utils.clifford_module.from_list import (
        add_single_qubit_gates_to_schedule,
        add_two_qubit_gates_to_schedule,
    )
except ImportError:
    logger.warning(
        "Could not find package: superconducting-qubit-tools.",
        "This is a proprietary licenced software.",
        "Please make sure that you are having a correct licence and install the dependency",
    )


class TQG_Randomized_Benchmarking(BaseMeasurement):
    def __init__(
        self,
        transmons: dict[str, ExtendedTransmon],
        couplers: dict[str, CompositeSquareEdge],
        qubit_state: int = 0,
    ):
        super().__init__(transmons)
        self.transmons = transmons
        self.qubit_state = qubit_state
        self.couplers = couplers

    def schedule_function(
        self,
        seed: int,
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
            name = "tqg_randomized_benchmarking"
        else:
            name = "tqg_randomized_benchmarking_interleaved"
        schedule = Schedule(name, repetitions)

        qubits = list(self.transmons.keys())
        coupler_names = self.couplers.keys()
        coupled_qubits = [coupler.split("_") for coupler in coupler_names]

        for index, this_coupler in enumerate(coupler_names):
            for index, this_coupler in enumerate(coupler_names):
                if this_coupler in ["q21_q22", "q22_q23", "q23_q24", "q24_q25"]:
                    downconvert = 0
                else:
                    downconvert = 4.4e9
                schedule.add_resource(
                    ClockResource(
                        name=f"{this_coupler}.cz",
                        freq=downconvert
                        - self.couplers[this_coupler].clock_freqs.cz_freq(),
                    )
                )

        print(self.couplers[this_coupler].clock_freqs.cz_freq())
        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Start")

        # The first for loop iterates over all qubits:
        # for this_qubit, clifford_sequence_lengths in number_of_cliffords.items():
        clifford_sequence_lengths = list(number_of_cliffords.values())[0]

        # all_cliffords = len(cliffords.XY_decompositions)
        # rng = np.random.default_rng(seed)

        # The inner for loop iterates over the random clifford sequence lengths
        for acq_index, this_number_of_cliffords in enumerate(
            clifford_sequence_lengths[:-3]
        ):
            # schedule.add(X(this_qubit))
            # random_sequence = rng.integers(all_cliffords, size=this_number_of_cliffords)

            start = schedule.add(IdlePulse(4e-9))

            # for clifford_index, sequence_index in enumerate(random_sequence):
            # n_cl = 1
            index = 0
            # seed = 42
            # interleaving_clifford_id = 4386 #CZ
            # interleaving_clifford_id = None
            # apply_inverse_gate = False
            # qubit_names_list = ['Q1', 'Q2']
            clifford_seq = randomized_benchmarking_sequence(
                n_cl=this_number_of_cliffords,
                meas_basis_index=index,
                seed=seed,
                interleaving_clifford_id=interleaving_clifford_id,
                apply_inverse_gate=apply_inverse_gate,
                number_of_qubits=2,
            )
            physical_gates = decompose_clifford_seq(clifford_seq, ["q23", "q24"])

            separation_time = 260e-9
            # schedule = Schedule('rb_sequence_generation')
            reset = schedule.add(Reset(*qubits))

            add_two_qubit_gates_to_schedule(
                schedule, physical_gates, ref_op=reset, separation_time=separation_time
            )

            buffer = schedule.add(IdlePulse(4e-9))
            for this_qubit in qubits:
                schedule.add(
                    Measure(this_qubit, acq_index=acq_index),
                    ref_op=buffer,
                    ref_pt="end",
                )
                end = schedule.add(Reset(this_qubit))

        for this_qubit in qubits:
            # 0 calibration point
            schedule.add(Reset(this_qubit), ref_op=end, ref_pt="end")
            schedule.add(Measure(this_qubit, acq_index=acq_index + 1))

            # 1 calibration point
            schedule.add(Reset(this_qubit))
            schedule.add(X(this_qubit))
            schedule.add(Measure(this_qubit, acq_index=acq_index + 2))
            schedule.add(Reset(this_qubit))

            # 2 calibration point
            schedule.add(Reset(this_qubit))
            schedule.add(Reset(this_qubit))
            schedule.add(X(this_qubit))
            schedule.add(Rxy_12(this_qubit))
            schedule.add(Measure(this_qubit, acq_index=acq_index + 3))
            schedule.add(Reset(this_qubit))
        return schedule
