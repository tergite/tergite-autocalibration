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

import numpy as np
from quantify_scheduler import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.gate_library import Reset, X90, Measure, X

from ....base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


class T2(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

    def schedule_function(
        self,
        delays: dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:
        """
        Generate a schedule for performing a T2 experiment measurement to find the coherence time T_2 for multiple qubits.

        Schedule sequence
            Reset -> pi/2 pulse -> Idel(tau) -> pi/2 pulse -> Measure

        Parameters
        ----------
        self
            Contains all qubit states.
        qubits
            The list of qubits on which to perform the experiment.
        delays
            Array of the sweeping delay times tau between the pi/2-pulse and the other pi/2-pulse for each qubit.
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """
        schedule = Schedule("multiplexed_T2", repetitions)

        qubits = self.transmons.keys()

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Start")

        # First loop over every qubit with corresponding tau sweeping lists
        for this_qubit, times_val in delays.items():
            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt="end"
            )  # To enforce parallelism we refer to the root relaxation

            # Second loop over all tau delay values
            for acq_index, tau in enumerate(times_val):
                schedule.add(X90(this_qubit))
                schedule.add(
                    X90(this_qubit),
                    ref_pt="end",
                    rel_time=tau,
                )
                schedule.add(
                    Measure(this_qubit, acq_index=acq_index, bin_mode=BinMode.AVERAGE)
                )
                schedule.add(Reset(this_qubit))
        return schedule


class T2Echo(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

    def schedule_function(
        self,
        delays: dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:
        """
        Generate a schedule for performing a T2 experiment measurement to find the coherence time T_2 for multiple qubits.

        Schedule sequence
            Reset -> pi/2 pulse -> Idel(tau) -> pi/2 pulse -> Measure

        Parameters
        ----------
        self
            Contains all qubit states.
        qubits
            The list of qubits on which to perform the experiment.
        delays
            Array of the sweeping delay times tau between the pi/2-pulse and the other pi/2-pulse for each qubit.
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """
        schedule = Schedule("multiplexed_T2_Echo", repetitions)

        qubits = self.transmons.keys()

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Start")

        # First loop over every qubit with corresponding tau sweeping lists
        for this_qubit, times_val in delays.items():
            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt="end"
            )  # To enforce parallelism we refer to the root relaxation

            # Second loop over all tau delay values
            for acq_index, tau in enumerate(times_val):
                schedule.add(X90(this_qubit))
                schedule.add(
                    X(this_qubit),
                    ref_pt="end",
                    rel_time=tau / 2,
                )
                schedule.add(
                    X90(this_qubit),
                    ref_pt="end",
                    rel_time=tau / 2,
                )
                schedule.add(
                    Measure(this_qubit, acq_index=acq_index, bin_mode=BinMode.AVERAGE)
                )
                schedule.add(Reset(this_qubit))
        return schedule
