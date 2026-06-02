# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2026
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
from quantify_scheduler.operations.gate_library import X90, Measure, Reset, Rxy, X
from quantify_scheduler.operations.pulse_library import IdlePulse

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.extended_coupler_edge import (
    ExtendedCompositeSquareEdge,
)
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


class ZZCouplingMeasurement(BaseMeasurement):
    def __init__(
        self,
        transmons: dict[str, ExtendedTransmon],
        couplers: dict[str, ExtendedCompositeSquareEdge],
    ):
        super().__init__(transmons)
        self.transmons = transmons
        self.couplers = couplers

    def schedule_function(
        self,
        artificial_detunings: dict[str, np.ndarray],
        ramsey_delays: dict[str, np.ndarray],
        spectator_states: dict[str, np.ndarray],
        coupler_dict: dict[str, dict],
        repetitions: int = 1024,
    ) -> Schedule:
        """
        Generate a schedule for performing a Ramsey fringe measurement on multiple qubits.
        Can be used both to finetune the qubit frequency and to measure the qubit dephasing time T_2. (1D parameter sweep)

        Schedule sequence
            Reset -> pi/2-pulse -> Idle(tau) -> pi/2-pulse -> Measure

        Parameters
        ----------
        artificial_detuning
            The artificial detuning of the qubit frequency, which is implemented by changing
            the phase of the second pi/2 pulse.
        ramsey_delays
            The wait times tau between the pi/2 pulses for each qubit
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """

        schedule_title = "zz-coupling"

        schedule = Schedule(schedule_title, repetitions)

        qubits = self.transmons.keys()
        couplers = self.couplers.keys()

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer loop, iterates over all couplers
        for this_coupler in couplers:
            active_qubit = coupler_dict[this_coupler]["active_qubit"]
            spectator_qubit = coupler_dict[this_coupler]["spectator_qubit"]
            this_transmon = self.transmons[active_qubit]
            mw_pulse_duration = this_transmon.rxy.duration()

            # To enforce parallelism we refer to the root relaxation
            schedule.add(Reset(active_qubit), ref_op=root_relaxation)

            art_detunings_values = artificial_detunings[active_qubit]
            ramsey_delays_values = ramsey_delays[active_qubit]
            spectator_state_values = spectator_states[this_coupler]
            number_of_inners = len(ramsey_delays_values)
            number_of_intermediates = len(art_detunings_values)

            for outer_index, spectator_state in enumerate(spectator_state_values):
                # The intermediate loop, iterates over all detunings
                for intermediate_index, detuning in enumerate(art_detunings_values):
                    # The inner for loop iterates over all delays
                    for inner_index, ramsey_delay in enumerate(ramsey_delays_values):
                        this_index = (
                            outer_index * (number_of_intermediates * number_of_inners)
                            + intermediate_index * number_of_inners
                            + inner_index
                        )

                        recovery_phase = np.rad2deg(2 * np.pi * detuning * ramsey_delay)

                        # TODO: this can be parallelized to the following X90
                        if spectator_state == 0:
                            schedule.add(IdlePulse(mw_pulse_duration))
                        elif spectator_state == 1:
                            schedule.add(X(spectator_qubit))
                        else:
                            raise ValueError(
                                f"Spectator state must be 0 or 1. Received {spectator_state}"
                            )

                        schedule.add(X90(active_qubit))

                        schedule.add(
                            Rxy(theta=90, phi=recovery_phase, qubit=active_qubit),
                            rel_time=ramsey_delay,
                        )

                        schedule.add(
                            Measure(
                                active_qubit,
                                acq_index=this_index,
                                bin_mode=BinMode.AVERAGE,
                            ),
                        )

                        schedule.add(Reset(active_qubit))
        return schedule
