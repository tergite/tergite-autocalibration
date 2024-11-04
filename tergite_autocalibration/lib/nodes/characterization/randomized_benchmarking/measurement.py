# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Amr Osman 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Module containing a schedule class for randomized benchmarking measurement.
"""
import numpy as np
from quantify_scheduler.operations.gate_library import Measure, Reset, Rxy, X
from quantify_scheduler.schedules.schedule import Schedule

import tergite_autocalibration.utils.clifford_elements_decomposition as cliffords
from tergite_autocalibration.utils.dto.extended_gates import Rxy_12
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon
from ....base.measurement import BaseMeasurement


class Randomized_Benchmarking(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

    def schedule_function(
        self,
        seeds: dict[str, int],
        number_of_cliffords: dict[str, np.ndarray],
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

        schedule = Schedule("multiplexed_randomized_benchmarking", repetitions)

        qubits = self.transmons.keys()

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Start")

        # The first for loop iterates over all qubits:
        for this_qubit, clifford_sequence_lengths in number_of_cliffords.items():
            all_cliffords = len(cliffords.XY_decompositions)
            seed = seeds[this_qubit]

            rng = np.random.default_rng(seed)

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt="end"
            )  # To enforce parallelism we refer to the root relaxation

            # The inner for loop iterates over the random clifford sequence lengths
            for acq_index, this_number_of_cliffords in enumerate(
                clifford_sequence_lengths[:-3]
            ):
                # schedule.add(X(this_qubit))
                random_sequence = rng.integers(
                    all_cliffords, size=this_number_of_cliffords
                )

                for sequence_index in random_sequence:
                    physical_gates = cliffords.XY_decompositions[sequence_index]
                    for gate_angles in physical_gates.values():
                        theta = gate_angles["theta"]
                        phi = gate_angles["phi"]
                        schedule.add(Rxy(qubit=this_qubit, theta=theta, phi=phi))

                recovery_index, recovery_XY_operations = cliffords.reversing_XY_matrix(
                    random_sequence
                )

                for gate_angles in recovery_XY_operations.values():
                    theta = gate_angles["theta"]
                    phi = gate_angles["phi"]
                    recovery_gate = schedule.add(
                        Rxy(qubit=this_qubit, theta=theta, phi=phi)
                    )

                schedule.add(
                    Measure(
                        this_qubit,
                        acq_index=acq_index,
                    ),
                    ref_op=recovery_gate,
                    ref_pt="end",
                )

                schedule.add(Reset(this_qubit))

            # 0 calibration point
            schedule.add(Reset(this_qubit))
            schedule.add(Reset(this_qubit))
            schedule.add(Measure(this_qubit, acq_index=acq_index + 1))
            schedule.add(Reset(this_qubit))

            # 1 calibration point
            schedule.add(Reset(this_qubit))
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
