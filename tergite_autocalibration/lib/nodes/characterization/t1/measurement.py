# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
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
Module containing a schedule class for T1 and T2 coherence time measurement.
"""
import numpy as np
from quantify_scheduler import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.gate_library import Measure, Reset, X

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


class T1(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

    def single_qubit_T1(
        self, schedule: Schedule, qubit: str, acq_index: int, tau: float
    ):
        schedule.add(X(qubit))
        schedule.add(
            Measure(qubit, acq_index=acq_index, bin_mode=BinMode.AVERAGE),
            ref_pt="end",
            rel_time=tau,
        )
        schedule.add(Reset(qubit))

    def schedule_function(
        self,
        delays: dict[str, np.ndarray],
        multiplexing: str = "parallel",
        repetitions: int = 1024,
    ) -> Schedule:
        """
        Generate a schedule for performing a T1 experiment measurement to find the relaxation time T_1 for multiple qubits.

        Schedule sequence
            Reset -> pi pulse -> Idel(tau) -> Measure

        Parameters
        ----------
        delays
            Array of the sweeping delay times tau between the pi-pulse and the measurement for each qubit.
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """
        schedule = Schedule("multiplexed_T1", repetitions)

        qubits = self.transmons.keys()

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Start")

        # First loop over every qubit
        for this_qubit, times_val in delays.items():
            if multiplexing == "parallel":
                schedule.add(
                    Reset(this_qubit), ref_op=root_relaxation, ref_pt="end"
                )  # To enforce parallelism we refer to the root relaxation
            elif multiplexing == "one_by_one":
                pass

            # Second loop over all tau delay values
            for acq_index, tau in enumerate(times_val):
                self.single_qubit_T1(schedule, this_qubit, acq_index, tau)

        return schedule
