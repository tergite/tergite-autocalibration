"""
Module containing a schedule class for DRAG pulse motzoi parameter calibration.
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler.resources import ClockResource
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.operations.gate_library import Measure, Reset
from calibration_schedules.measurement_base import Measurement
import numpy as np

class Motzoi_parameter(Measurement):

    def __init__(self,transmons,qubit_state=0):
        super().__init__(transmons)
        self.transmons = transmons
        self.static_kwargs = {
            'qubits': self.qubits,
            'mw_frequencies': self.attributes_dictionary('f01'),
            'mw_amplitudes': self.attributes_dictionary('amp180'),
            'mw_pulse_durations': self.attributes_dictionary('duration'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
        }

    def schedule_function(
            self, #Note, this is not used in the schedule
            qubits: list[str],
            mw_frequencies: dict[str,float],
            mw_amplitudes: dict[str,float],
            mw_pulse_ports: dict[str,str],
            mw_pulse_durations: dict[str,float],
            mw_motzois: dict[str,np.ndarray],
            X_repetitions: dict[str,np.ndarray],
            repetitions: int = 1024,
        ) -> Schedule:
        """
        Generate a schedule for a DRAG pulse calibration measurement that gives the optimized motzoi parameter.
        This calibrates the drive pulse as to account for errors caused by higher order excitations of the qubits.

        Schedule sequence
            Reset -> DRAG pulse -> Inverse DRAG pulse -> Measure
        Note: Step 2 and 3 are repeated X_repetition amount of times

        Parameters
        ----------
        self
            Contains all qubit states.
        qubits
            The list of qubits on which to perform the experiment.
        mw_frequencies
            Frequency of the DRAG pulse for each qubit.
        mw_amplitudes
           Amplitude of the DRAG pulse for each qubit.
        mw_pulse_ports
            Location on the device where the DRAG pulse is applied.
        mw_clocks
            Clock that the frequency of the DRAG pulse is assigned to for each qubit.
        mw_pulse_durations
            Duration of the DRAG pulse for each qubit.
        repetitions
            The amount of times the Schedule will be repeated.
        **mw_motzois
            2D sweeping parameter arrays.
            X_repetition: The amount of times that the DRAG pulse and inverse DRAG pulse are applied
            mw_motzoi: The mozoi parameter values of the DRAG (and inverse DRAG) pulses.

        Returns
        -------
        :
            An experiment schedule.
        """
        schedule = Schedule("mltplx_motzoi",repetitions)

        for this_qubit, mw_f_val in mw_frequencies.items():
            schedule.add_resource(
                ClockResource( name=f'{this_qubit}.01', freq=mw_f_val)
            )

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer loop, iterates over all qubits
        for this_qubit, X_values in X_repetitions.items():
            this_clock = f'{this_qubit}.01'

            motzoi_parameter_values = mw_motzois[this_qubit]
            number_of_motzois = len(motzoi_parameter_values)

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            # The intermediate loop iterates over all numbers of X pulses
            for x_index, this_x in enumerate(X_values):

                # The inner for loop iterates over all motzoi values
                for motzoi_index, mw_motzoi in enumerate(motzoi_parameter_values):
                    this_index = x_index*number_of_motzois + motzoi_index
                    for _ in range(this_x):
                        schedule.add(
                            DRAGPulse(
                                duration=mw_pulse_durations[this_qubit],
                                G_amp=mw_amplitudes[this_qubit],
                                D_amp=mw_motzoi,
                                port=mw_pulse_ports[this_qubit],
                                clock=this_clock,
                                phase=0,
                            ),
                        )
                        # inversion pulse requires 180 deg phase
                        schedule.add(
                            DRAGPulse(
                                duration=mw_pulse_durations[this_qubit],
                                G_amp=mw_amplitudes[this_qubit],
                                D_amp=mw_motzoi,
                                port=mw_pulse_ports[this_qubit],
                                clock=this_clock,
                                phase=180,
                            ),
                        )

                    schedule.add(
                        Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                    )

                    schedule.add(Reset(this_qubit))

        return schedule
