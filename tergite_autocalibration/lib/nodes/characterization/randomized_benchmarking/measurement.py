# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Chalmers Next Labs 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
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
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.control_flow_library import Loop
from quantify_scheduler.operations.gate_library import Reset, Rxy
from quantify_scheduler.operations.pulse_library import IdlePulse
from quantify_scheduler.schedules.schedule import Schedule

import tergite_autocalibration.utils.clifford_elements_decomposition as cliffords
from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.extended_gates import Measure_RO_3state_Opt
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


class Randomized_Benchmarking_SSRO(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)
        self.transmons = transmons
        self.qubit_state = qubit_state

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

    def rb_shot(
        self,
        seeds: dict[str, int],
        number_of_cliffords: dict[str, np.ndarray],
    ):
        shot = Schedule("shot")
        shot.add(IdlePulse(16e-9))

        qubits = list(self.transmons.keys())

        root_relaxation = shot.add(Reset(*qubits), label="Start")

        clifford_sequence_lengths = list(number_of_cliffords.values())[0]

        # for single qubits all_cliffords = 24
        all_cliffords = len(cliffords.XY_decompositions)

        # The outer for loop iterates over all qubits:
        for this_qubit, clifford_sequence_lengths in number_of_cliffords.items():
            seed = seeds[this_qubit]  # this is just an integer

            rng = np.random.default_rng(seed)  # this is a generator

            shot.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt="end"
            )  # To enforce parallelism we refer to the root relaxation

            # The inner for loop iterates over the random clifford sequence lengths
            for acq_index, this_number_of_cliffords in enumerate(
                clifford_sequence_lengths
            ):
                random_sequence = rng.integers(
                    all_cliffords, size=this_number_of_cliffords
                )  # for example if this_number_of_cliffords=4 , a random_sequence could be [5, 14, 19, 23]

                for sequence_index in random_sequence:
                    physical_gates = cliffords.XY_decompositions[sequence_index]
                    for gate_angles in physical_gates.values():
                        theta = gate_angles["theta"]
                        phi = gate_angles["phi"]
                        shot.add(Rxy(qubit=this_qubit, theta=theta, phi=phi))

                _, recovery_XY_operations = cliffords.reversing_XY_matrix(
                    random_sequence
                )

                for gate_angles in recovery_XY_operations.values():
                    theta = gate_angles["theta"]
                    phi = gate_angles["phi"]
                    shot.add(Rxy(qubit=this_qubit, theta=theta, phi=phi))

                shot.add(
                    Measure_RO_3state_Opt(
                        this_qubit, acq_index=acq_index, bin_mode=BinMode.APPEND
                    ),
                )

                shot.add(Reset(this_qubit))

        return shot

    def schedule_function(
        self,
        seeds: dict[str, int],
        number_of_cliffords: dict[str, np.ndarray],
        loop_repetitions: int,
    ) -> Schedule:
        schedule = Schedule("multiplexed_randomized_benchmarking", repetitions=1)

        rb_shot_schedule = self.rb_shot(seeds, number_of_cliffords)

        schedule.add(rb_shot_schedule, control_flow=Loop(loop_repetitions))
        schedule.add(IdlePulse(20e-9))
        return schedule
