# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
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
Module containing a schedule class for Rabi calibration.
"""
import numpy as np
from quantify_scheduler import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.resources import ClockResource

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.extended_gates import Measure_RO1
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


class Rabi_Oscillations(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

    def schedule_function(
        self,
        mw_amplitudes: dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:
        """
        Generate a schedule for performing a Rabi oscillation measurement on multiple qubits using a Gaussian pulse.

        Schedule sequence
            Reset -> Gaussian pulse -> Measure
        Parameters

        ----------
        mw_amplitudes
            Array of the sweeping amplitudes of the Rabi pulse for each qubit.
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """
        if self.qubit_state == 0:
            schedule_title = "multiplexed_rabi_01"
            measure_function = Measure
        elif self.qubit_state == 1:
            schedule_title = "multiplexed_rabi_12"
            measure_function = Measure_RO1
        else:
            raise ValueError(f"Invalid qubit state: {self.qubit_state}")

        schedule = Schedule(schedule_title, repetitions)

        qubits = self.transmons.keys()

        # we must first add the clocks
        if self.qubit_state == 0:
            for this_qubit, this_transmon in self.transmons.items():
                mw_frequency_01 = this_transmon.clock_freqs.f01()
                this_clock = f"{this_qubit}.01"
                schedule.add_resource(
                    ClockResource(name=this_clock, freq=mw_frequency_01)
                )
        elif self.qubit_state == 1:
            for this_qubit, this_transmon in self.transmons.items():
                mw_frequency_12 = this_transmon.clock_freqs.f12()
                this_clock = f"{this_qubit}.12"
                schedule.add_resource(
                    ClockResource(name=this_clock, freq=mw_frequency_12)
                )
        else:
            raise ValueError(f"Invalid qubit state: {self.qubit_state}")

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        for this_qubit, mw_amp_array_val in mw_amplitudes.items():
            # unpack the static parameters
            this_transmon = self.transmons[this_qubit]
            mw_pulse_duration = this_transmon.rxy.duration()
            mw_pulse_port = this_transmon.ports.microwave()

            if self.qubit_state == 0:
                this_clock = f"{this_qubit}.01"
            elif self.qubit_state == 1:
                this_clock = f"{this_qubit}.12"
            else:
                raise ValueError(f"Invalid qubit state: {self.qubit_state}")

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt="end"
            )  # To enforce parallelism we refer to the root relaxation

            # The second for loop iterates over all amplitude values in the amplitudes batch:
            for acq_index, mw_amplitude in enumerate(mw_amp_array_val):
                if self.qubit_state == 1:
                    schedule.add(X(this_qubit))
                schedule.add(
                    DRAGPulse(
                        duration=mw_pulse_duration,
                        G_amp=mw_amplitude,
                        D_amp=0,
                        port=mw_pulse_port,
                        clock=this_clock,
                        phase=0,
                    ),
                )

                schedule.add(
                    measure_function(
                        this_qubit, acq_index=acq_index, bin_mode=BinMode.AVERAGE
                    ),
                )

                schedule.add(Reset(this_qubit))

        return schedule


class N_Rabi_Oscillations(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

    def schedule_function(
        self,
        mw_amplitudes_sweep: dict[str, np.ndarray],
        X_repetitions: dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:
        """

        Schedule sequence
            Reset -> DRAG pulse x N times-> Measure
        Step 2 and 3 are repeated X_repetition amount of times

        Parameters
        ----------
        mw_amplitudes
        X_repetition: The amount of times that the DRAG pulse and inverse DRAG pulse are applied
           mw_amplitude: Amplitude of the DRAG pulse for each qubit.
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """
        if self.qubit_state == 0:
            schedule_title = "mltplx_nrabi_01"
            measure_function = Measure
        elif self.qubit_state == 1:
            schedule_title = "mltplx_nrabi_12"
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
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer loop, iterates over all qubits
        for this_qubit, X_values in X_repetitions.items():
            this_transmon = self.transmons[this_qubit]
            mw_pulse_duration = this_transmon.rxy.duration()
            mw_pulse_port = this_transmon.ports.microwave()
            mw_amplitude = this_transmon.rxy.amp180()
            mw_motzoi = this_transmon.rxy.motzoi()

            this_clock = f"{this_qubit}.01"

            if self.qubit_state == 1:
                mw_amplitude = this_transmon.r12.ef_amp180()
                mw_motzoi = this_transmon.r12.ef_motzoi()
                this_clock = f"{this_qubit}.12"
                measure_function = Measure_RO1
            elif self.qubit_state == 0:
                measure_function = Measure
                this_clock = f"{this_qubit}.01"
            else:
                raise ValueError(f"Invalid qubit state: {self.qubit_state}")

            mw_amplitudes_values = mw_amplitudes_sweep[this_qubit]
            number_of_amplitudes = len(mw_amplitudes_values)

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new="end"
            )  # To enforce parallelism we refer to the root relaxation

            # The intermediate loop iterates over all amplitude values:
            for x_index, this_x in enumerate(X_values):
                # The inner for loop iterates over all frequency values in the frequency batch:
                for mw_amplitude_index, mw_amplitude_correction in enumerate(
                    mw_amplitudes_values
                ):
                    this_index = x_index * number_of_amplitudes + mw_amplitude_index
                    if self.qubit_state == 1:
                        schedule.add(X(this_qubit))
                    for _ in range(this_x):
                        schedule.add(
                            DRAGPulse(
                                duration=mw_pulse_duration,
                                G_amp=mw_amplitude + mw_amplitude_correction,
                                D_amp=mw_motzoi,
                                port=mw_pulse_port,
                                clock=this_clock,
                                phase=0,
                            ),
                        )
                        schedule.add(
                            DRAGPulse(
                                duration=mw_pulse_duration,
                                G_amp=mw_amplitude + mw_amplitude_correction,
                                D_amp=mw_motzoi,
                                port=mw_pulse_port,
                                clock=this_clock,
                                phase=0,
                            ),
                        )
                        if self.qubit_state == 0:
                            schedule.add(
                                DRAGPulse(
                                    duration=mw_pulse_duration,
                                    G_amp=mw_amplitude + mw_amplitude_correction,
                                    D_amp=mw_motzoi,
                                    port=mw_pulse_port,
                                    clock=this_clock,
                                    phase=90,
                                ),
                            )
                            schedule.add(
                                DRAGPulse(
                                    duration=mw_pulse_duration,
                                    G_amp=mw_amplitude + mw_amplitude_correction,
                                    D_amp=mw_motzoi,
                                    port=mw_pulse_port,
                                    clock=this_clock,
                                    phase=90,
                                ),
                            )

                    schedule.add(
                        measure_function(
                            this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE
                        ),
                    )

                    schedule.add(Reset(this_qubit))

        return schedule
