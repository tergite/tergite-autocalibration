"""
Module containing a schedule class for Ramsey calibration. (1D parameter sweep, for 2D see ramsey_detunings.py)
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.resources import ClockResource
from tergite_autocalibration.lib.measurement_base import Measurement
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon, Measure_RO1

import numpy as np

class Ramsey_fringes(Measurement):

    def __init__(self,transmons: dict[str, ExtendedTransmon],qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state

    def schedule_function(
            self,
            artificial_detunings: dict[str,np.ndarray],
            ramsey_delays: dict[str,np.ndarray],
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

        if self.qubit_state == 0:
            schedule_title = "multiplexed_ramsey_01"
            measure_function = Measure
        elif self.qubit_state == 1:
            schedule_title = "multiplexed_ramsey_12"
            measure_function = Measure_RO1
        else:
            raise ValueError(f'Invalid qubit state: {self.qubit_state}')

        schedule = Schedule(schedule_title,repetitions)

        qubits = self.transmons.keys()

        if self.qubit_state == 1:
            for this_qubit, this_transmon in self.transmons.items():
                mw_frequency_12 = this_transmon.clock_freqs.f12()
                this_clock = f'{this_qubit}.12'
                schedule.add_resource(ClockResource(name=this_clock, freq=mw_frequency_12))

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer loop, iterates over all qubits
        for this_qubit, artificial_detunings_values in artificial_detunings.items():
            this_transmon = self.transmons[this_qubit]
            mw_pulse_duration = this_transmon.rxy.duration()
            mw_pulse_port = this_transmon.ports.microwave()
            mw_ef_amp180 = this_transmon.r12.ef_amp180()

            if self.qubit_state == 1:
                this_clock = f'{this_qubit}.12'
                measure_function = Measure_RO1
            elif self.qubit_state == 0:
                measure_function = Measure
                this_clock = f'{this_qubit}.01'
            else:
                raise ValueError(f'Invalid qubit state: {self.qubit_state}')

            schedule.add(
                    Reset(*qubits), ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            ramsey_delays_values = ramsey_delays[this_qubit]
            number_of_delays = len(ramsey_delays_values)

            # The intermediate loop, iterates over all detunings
            for detuning_index, detuning in enumerate(artificial_detunings_values):

                # The inner for loop iterates over all delays
                for acq_index, ramsey_delay in enumerate(ramsey_delays_values):

                    this_index = detuning_index*number_of_delays + acq_index

                    recovery_phase = np.rad2deg(2 * np.pi * detuning * ramsey_delay)

                    if self.qubit_state == 1:
                        schedule.add(X(this_qubit))
                        f12_amp = mw_ef_amp180
                        schedule.add(
                            DRAGPulse(
                                duration=mw_pulse_duration,
                                G_amp=f12_amp/2,
                                D_amp=0,
                                port=mw_pulse_port,
                                clock=this_clock,
                                phase=0,
                            ),
                        )

                        schedule.add(
                            DRAGPulse(
                                duration=mw_pulse_duration,
                                G_amp=f12_amp/2,
                                D_amp=0,
                                port=mw_pulse_port,
                                clock=this_clock,

                                phase=recovery_phase,
                            ),
                            rel_time=ramsey_delay
                        )

                    if self.qubit_state == 0:

                        schedule.add(X90(this_qubit))

                        schedule.add(
                            Rxy(theta=90, phi=recovery_phase, qubit=this_qubit),
                            rel_time=ramsey_delay
                        )

                    schedule.add(
                        measure_function(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                    )

                    schedule.add(Reset(this_qubit))
        return schedule
