"""
Module containing a schedule class for punchout (readout amplitude) calibration.
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.resources import ClockResource
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import SquarePulse, SetClockFrequency
from quantify_scheduler.operations.gate_library import Reset
from calibration_schedules.measurement_base import Measurement
import numpy as np


class Punchout(Measurement):

    def __init__(self,transmons,qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

        self.static_kwargs = {
            'qubits': self.qubits,
            'pulse_durations': self.attributes_dictionary('pulse_duration'),
            'acquisition_delays': self.attributes_dictionary('acq_delay'),
            'integration_times': self.attributes_dictionary('integration_time'),
            'ports': self.attributes_dictionary('readout_port'),
        }


    def schedule_function(
            self, #Note, this is not used in the schedule
            qubits: list[str],
            pulse_durations: dict[str,float],
            acquisition_delays: dict[str,float],
            integration_times: dict[str,float],
            ports: dict[str,str],
            ro_frequencies: dict[str,np.ndarray],
            ro_amplitudes: dict[str,np.ndarray],
            repetitions: int = 1024,
        ) -> Schedule:
        """
        Generate a schedule for performing a punchout spectroscopy mainly used to calibrate the amplitude of the readout pulse.

        Schedule sequence
            Reset -> Spectroscopy readout pulse -> SSBIntegrationComplex (Measurement)
        Note: Similar to resonator spectroscopy, but here the amplitude of the readout pulse is also a sweeping parameter.

        Parameters
        ----------
        self
            Contains all qubit states.
        qubits
            The list of qubits on which to perform the experiment.
        pulse_durations
            Duration of the readout pulse for each qubit.
        acquisition_delays
            Start of data acquisition relative to the start of the readout pulse for each qubit.
        integration_times
            Integration time of the data acquisition for each qubit.
        ports
            Location on the device where the readout pulse is applied for each qubit.
        ro_frequencies
            Array of the sweeping frequencies of the readout pulse for each qubit.
        ro_amplitudes
            Array of the sweeping amplitudes of the readout pulse for each qubit.
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """

        schedule = Schedule("mltplx_punchout",repetitions)

        # Initialize the clock for each qubit
        for this_qubit, ro_array_val in ro_frequencies.items():

            #Initialize ClockResource with the first frequency value
            schedule.add_resource( ClockResource(name=f'{this_qubit}.ro', freq=ro_array_val[0]) )

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer loop, iterates over all qubits
        for acq_cha, (this_qubit, ro_amplitude_values) in enumerate(ro_amplitudes.items()):
            this_clock = f'{this_qubit}.ro'

            frequency_values = ro_frequencies[this_qubit]
            number_of_freqs = len(frequency_values)

            schedule.add(
                    Reset(*qubits), ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            # The intermediate loop, iterates over all ro_amplitudes
            for ampl_indx, ro_amplitude in enumerate(ro_amplitude_values):

                #The inner for loop iterates over all frequency values in the frequency batch:
                for acq_index, ro_freq in enumerate(ro_frequencies[this_qubit]):
                    this_index = ampl_indx*number_of_freqs + acq_index

                    schedule.add(
                        SetClockFrequency(clock=this_clock, clock_freq_new=ro_freq),
                    )

                    schedule.add(
                        SquarePulse(
                            duration=pulse_durations[this_qubit],
                            amp=ro_amplitude,
                            port=ports[this_qubit],
                            clock=this_clock,
                        ),
                        ref_pt="end",
                    )

                    schedule.add(
                        SSBIntegrationComplex(
                            duration=integration_times[this_qubit],
                            port=ports[this_qubit],
                            clock=this_clock,
                            acq_index=this_index,
                            acq_channel=acq_cha,
                            bin_mode=BinMode.AVERAGE
                        ),
                        ref_pt="start",
                        rel_time=acquisition_delays[this_qubit],
                        label=f"acquisition_{this_qubit}_{this_index}",
                    )

                    schedule.add(Reset(this_qubit))

        return schedule
