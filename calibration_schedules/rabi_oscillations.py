"""
Module containing a schedule class for Rabi calibration.
"""
from quantify_scheduler.resources import ClockResource
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from utilities.extended_transmon_element import Measure_RO1
from calibration_schedules.measurement_base import Measurement
import numpy as np


class Rabi_Oscillations(Measurement):

    def __init__(self, transmons, qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

        self.static_kwargs = {
            'qubits': self.qubits,
            'mw_frequencies_01': self.attributes_dictionary('f01'),
            'mw_frequencies_12': self.attributes_dictionary('f12'),
            'mw_pulse_durations': self.attributes_dictionary('duration'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
        }

    def schedule_function(
        self,
        qubits: list[str],
        mw_frequencies_01: dict[str, float],
        mw_frequencies_12: dict[str, float],
        mw_pulse_durations: dict[str, float],
        mw_pulse_ports: dict[str, str],
        mw_amplitudes: dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:
        """
        Generate a schedule for performing a Rabi oscillation measurement on multiple qubits using a Gaussian pulse.

        Schedule sequence
            Reset -> Gaussian pulse -> Measure
        Parameters

        ----------
        self
            Contains all qubit states.
        qubits
            The list of qubits on which to perform the experiment.
        mw_pulse_durations
            Duration of the Gaussian shaped Rabi pulse for each qubit.
        mw_pulse_ports
            Location on the device where the Rabi pulse is applied for each qubit.
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
            raise ValueError(f'Invalid qubit state: {self.qubit_state}')

        schedule = Schedule(schedule_title, repetitions)

        # we must first add the clocks
        if self.qubit_state == 0:
            for this_qubit, mw_f_val in mw_frequencies_01.items():
                this_clock = f'{this_qubit}.01'
                schedule.add_resource(ClockResource(name=this_clock, freq=mw_f_val))
        elif self.qubit_state == 1:
            for this_qubit, mw_f_val in mw_frequencies_12.items():
                this_clock = f'{this_qubit}.12'
                schedule.add_resource(ClockResource(name=this_clock, freq=mw_f_val))
        else:
            raise ValueError(f'Invalid qubit state: {self.qubit_state}')

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        for this_qubit, mw_amp_array_val in mw_amplitudes.items():
            if self.qubit_state == 0:
                this_clock = f'{this_qubit}.01'
            elif self.qubit_state == 1:
                this_clock = f'{this_qubit}.12'
            else:
                raise ValueError(f'Invalid qubit state: {self.qubit_state}')

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt='end'
            )  # To enforce parallelism we refer to the root relaxation

            # The second for loop iterates over all amplitude values in the amplitudes batch:
            for acq_index, mw_amplitude in enumerate(mw_amp_array_val):
                if self.qubit_state == 1:
                    schedule.add(X(this_qubit))
                schedule.add(
                    DRAGPulse(
                        duration=mw_pulse_durations[this_qubit],
                        G_amp=mw_amplitude,
                        D_amp=0,
                        port=mw_pulse_ports[this_qubit],
                        clock=this_clock,
                        phase=0,
                    ),
                )

                schedule.add(
                    measure_function(this_qubit, acq_index=acq_index, bin_mode=BinMode.AVERAGE),
                )

                schedule.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{acq_index}")

        return schedule
