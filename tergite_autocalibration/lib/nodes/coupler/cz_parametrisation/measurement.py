# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2024
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
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from quantify_scheduler.operations.pulse_library import IdlePulse
from quantify_scheduler.operations.pulse_library import (
    SetClockFrequency,
    SoftSquarePulse,
    ResetClockPhase,
)
from quantify_scheduler.resources import ClockResource

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.extended_coupler_edge import ExtendedCompositeSquareEdge
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon


class CZParametrisationFixDuration(BaseMeasurement):
    def __init__(
        self,
        transmons: dict[str, ExtendedTransmon],
        couplers: dict[str, ExtendedCompositeSquareEdge],
        qubit_state: int = 0,
    ):
        super().__init__(transmons)
        self.transmons = transmons
        self.qubit_state = qubit_state
        self.couplers = couplers
        self.cz_pulse_duration = 240e-9

    def schedule_function(
        self,
        cz_pulse_frequencies: dict[str, np.ndarray],
        cz_pulse_amplitudes: dict[str, np.ndarray],
        cz_parking_currents: dict[str, float],
    ) -> Schedule:
        """
        Generate a schedule for performing a Ramsey fringe measurement on multiple qubits.
        Can be used both to finetune the qubit frequency and to measure the qubit dephasing time T_2. (1D parameter sweep)

        Schedule sequence
            Reset -> pi/2-pulse -> Idle(tau) -> pi/2-pulse -> Measure

        Parameters
        ----------
        self
            Contains all qubit states.
        qubits
            A list of two qubits to perform the experiment on. i.e. [['q1','q2'],['q3','q4'],...]
        mw_clocks_12
            Clocks for the 12 transition frequency of the qubits.
        mw_ef_amps180
            Amplitudes used for the excitation of the qubits to calibrate for the 12 transition.
        mw_frequencies_12
            Frequencies used for the excitation of the qubits to calibrate for the 12 transition.
        mw_pulse_ports
            Location on the device where the pulsed used for excitation of the qubits to calibrate for the 12 transition is located.
        mw_pulse_durations
            Pulse durations used for the excitation of the qubits to calibrate for the 12 transition.
        cz_pulse_frequency
            The frequency of the CZ pulse.
        cz_pulse_amplitude
            The amplitude of the CZ pulse.
        cz_pulse_duration
            The duration of the CZ pulse.
        cz_pulse_width
            The width of the CZ pulse.
        testing_group
            The edge group to be tested. 0 means all edges.
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """
        self.schedule = Schedule("CZ_Frequency_And_Amplitude")

        cz_frequency_values = np.array(list(cz_pulse_frequencies.values())[0])
        cz_amplitude_values = list(cz_pulse_amplitudes.values())[0]

        self.loop_frequencies_and_aplitudes(cz_amplitude_values, cz_frequency_values)

        return self.schedule

    def loop_frequencies_and_aplitudes(self, cz_amplitude_values, cz_frequency_values):
        for coupler in self.couplers:
            if coupler in ["q21_q22", "q22_q23", "q23_q24", "q24_q25"]:
                downconvert = 0
            else:
                downconvert = 4.4e9
            self.schedule.add_resource(
                ClockResource(
                    name=coupler + ".cz", freq=-cz_frequency_values[0] + downconvert
                )
            )

            # The outer loop, iterates over all cz_frequencies
            for freq_index, cz_frequency in enumerate(cz_frequency_values):
                cz_clock = f"{coupler}.cz"
                self.schedule.add(
                    SetClockFrequency(
                        clock=cz_clock, clock_freq_new=-cz_frequency + downconvert
                    ),
                )
                self.loop_amplitudes(coupler, cz_amplitude_values, freq_index)

    def loop_amplitudes(self, coupler, cz_amplitude_values, freq_index):
        # The inner for loop iterates over cz pulse amplitude
        number_of_amplitudess = len(cz_amplitude_values)
        qubits = coupler.split(sep="_")
        for acq_index, cz_amplitude in enumerate(cz_amplitude_values):
            this_index = freq_index * number_of_amplitudess + acq_index

            relaxation = self.schedule.add(Reset(*qubits))

            for this_qubit in qubits:
                self.schedule.add(X(this_qubit), ref_op=relaxation, ref_pt="end")

            buffer = self.schedule.add(IdlePulse(4e-9))

            self.schedule.add(ResetClockPhase(clock=coupler + ".cz"))
            cz_clock = f"{coupler}.cz"
            cz_pulse_port = f"{coupler}:fl"

            self.schedule.add(
                SoftSquarePulse(
                    duration=self.cz_pulse_duration,
                    amp=cz_amplitude,
                    port=cz_pulse_port,
                    clock=cz_clock,
                ),
            )
            buffer = self.schedule.add(IdlePulse(4e-9))

            for this_qubit in qubits:
                # logger.info(f"Add measure to {this_qubit}")
                self.schedule.add(
                    Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                    ref_op=buffer,
                    rel_time=4e-9,
                    ref_pt="end",
                )
