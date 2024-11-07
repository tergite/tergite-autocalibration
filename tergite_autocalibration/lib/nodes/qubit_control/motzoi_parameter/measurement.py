# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Module containing a schedule class for DRAG pulse motzoi parameter calibration.
"""
from __future__ import annotations

import numpy as np
from quantify_scheduler import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.resources import ClockResource

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.extended_gates import Measure_RO1
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon


class Motzoi_parameter(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

    def schedule_function(
        self,
        mw_motzois: dict[str, np.ndarray],
        X_repetitions: int | dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:
        """
        Generate a schedule for a DRAG pulse calibration measurement that gives the optimized motzoi parameter.
        This calibrates the drive pulse as to account for errors caused by higher order excitations of the qubits.

        Schedule sequence
            Reset -> DRAG pulse -> Inverse DRAG pulse -> Measure
        Step 2 and 3 are repeated X_repetition amount of times


        Parameters
        ----------
        repetitions
            The amount of times the Schedule will be repeated.
        mw_motzois
            2D sweeping parameter arrays.
        X_repetition: The amount of times that the DRAG pulse and inverse DRAG pulse are applied
            mw_motzoi: The mozoi parameter values of the DRAG (and inverse DRAG) pulses.

        Returns
        -------
        :
            An experiment schedule.
        """
        if self.qubit_state == 0:
            schedule_title = "mltplx_motzoi_01"
            measure_function = Measure
        elif self.qubit_state == 1:
            schedule_title = "mltplx_motzoi_12"
            measure_function = Measure_RO1
        else:
            raise ValueError(f"Invalid qubit state: {self.qubit_state}")
        schedule = Schedule(schedule_title, repetitions)

        qubits = self.transmons.keys()

        for this_qubit, this_transmon in self.transmons.items():
            mw_frequency = this_transmon.clock_freqs.f01()
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.01", freq=mw_frequency)
            )
            if self.qubit_state == 1:
                mw_frequency_12 = this_transmon.clock_freqs.f12()
                this_clock = f"{this_qubit}.12"
                schedule.add_resource(
                    ClockResource(name=this_clock, freq=mw_frequency_12)
                )

        # This is the common reference operation so the qubits can be operated in parallel
        # FIXME: This should be configurable, quantify-scheduler 0.21.1 does seem to need a duration multiple of 4ns
        root_relaxation = schedule.add(Reset(*qubits, duration=4e-9), label="Reset")

        # The outer loop, iterates over all qubits
        for this_qubit, X_values in X_repetitions.items():
            this_transmon = self.transmons[this_qubit]
            mw_amplitude = this_transmon.rxy.amp180()
            mw_pulse_duration = this_transmon.rxy.duration()
            mw_pulse_port = this_transmon.ports.microwave()

            this_clock = f"{this_qubit}.01"

            motzoi_parameter_values = mw_motzois[this_qubit]
            number_of_motzois = len(motzoi_parameter_values)

            if self.qubit_state == 1:
                mw_amplitude = this_transmon.r12.ef_amp180()
                this_clock = f"{this_qubit}.12"
                measure_function = Measure_RO1
            elif self.qubit_state == 0:
                measure_function = Measure
                this_clock = f"{this_qubit}.01"
            else:
                raise ValueError(f"Invalid qubit state: {self.qubit_state}")

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new="end"
            )  # To enforce parallelism we refer to the root relaxation

            # The intermediate loop iterates over all numbers of X pulses
            for x_index, this_x in enumerate(X_values):
                # The inner for loop iterates over all motzoi values
                for motzoi_index, mw_motzoi in enumerate(motzoi_parameter_values):
                    this_index = x_index * number_of_motzois + motzoi_index
                    if self.qubit_state == 1:
                        schedule.add(X(this_qubit))
                    for _ in range(this_x):
                        schedule.add(
                            DRAGPulse(
                                duration=mw_pulse_duration,
                                G_amp=mw_amplitude,
                                D_amp=mw_motzoi,
                                port=mw_pulse_port,
                                clock=this_clock,
                                phase=0,
                            ),
                        )
                        # inversion pulse requires 180 deg phase
                        schedule.add(
                            DRAGPulse(
                                duration=mw_pulse_duration,
                                G_amp=mw_amplitude,
                                D_amp=mw_motzoi,
                                port=mw_pulse_port,
                                clock=this_clock,
                                phase=180,
                            ),
                        )

                        if self.qubit_state == 0:
                            schedule.add(
                                DRAGPulse(
                                    duration=mw_pulse_duration,
                                    G_amp=mw_amplitude,
                                    D_amp=mw_motzoi,
                                    port=mw_pulse_port,
                                    clock=this_clock,
                                    phase=90,
                                ),
                            )
                            # inversion pulse requires 180 deg phase
                            schedule.add(
                                DRAGPulse(
                                    duration=mw_pulse_duration,
                                    G_amp=mw_amplitude,
                                    D_amp=mw_motzoi,
                                    port=mw_pulse_port,
                                    clock=this_clock,
                                    phase=270,
                                ),
                            )

                    schedule.add(
                        measure_function(
                            this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE
                        ),
                    )

                    schedule.add(Reset(this_qubit))

        return schedule
