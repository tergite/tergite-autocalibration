"""
Module containing a schedule class for two-tone (qubit) spectroscopy calibration.
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from quantify_scheduler.operations.pulse_library import SetClockFrequency, SoftSquarePulse
from quantify_scheduler.operations.pulse_factories import long_square_pulse
from quantify_scheduler.resources import ClockResource
from quantify_scheduler.schedules.schedule import Schedule
from utilities.extended_transmon_element import Measure_RO1
import numpy as np

from calibration_schedules.measurement_base import Measurement

class Two_Tones_Multidim(Measurement):

    def __init__(self,transmons,qubit_state:int=0):
        super().__init__(transmons)

        self.qubit_state = qubit_state
        self.transmons = transmons

        self.static_kwargs = {
            'qubits': self.qubits,
            'spec_pulse_durations': self.attributes_dictionary('spec_duration'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
        }


    def schedule_function(
        self,
        qubits: list[str],
        spec_pulse_durations: dict[str,float],
        mw_pulse_ports: dict[str,str],
        spec_frequencies: dict[str,np.ndarray],
        spec_pulse_amplitudes: dict[str,np.ndarray],

        repetitions: int = 1024,
        ) -> Schedule:
        """
        Generate a schedule for performing two-tone (qubit) spectroscopy to locate the qubits resonance frequency for multiple qubits.

        Schedule sequence
            Reset -> Spectroscopy pulse -> Measure
        
        Parameters
        ----------
        self
            Contains all qubit states.
        qubits
            The list of qubits that are calibrated.
        mw_pulse_durations
            Duration of the spectroscopy pulse for each qubit.
        mw_pulse_amplitudes
            Amplitude of the spectroscopy pulse for each qubit.
        mw_pulse_ports
            Location on the device where the spectroscopy pulse is applied for each qubit.
        mw_frequencies
            The sweeping frequencies of the spectroscopy pulse for each qubit.
        repetitions
            The amount of times the Schedule will be repeated.
        
        Returns
        -------
        :
            An experiment schedule.
        """

        # if port_out is None: port_out = port
        schedule = Schedule("multiplexed_qubit_spec",repetitions)
        
        # Initialize the clock for each qubit
        for this_qubit, spec_array_val in spec_frequencies.items():

            #Initialize ClockResource with the first frequency value
            schedule.add_resource( ClockResource(name=f'{this_qubit}.01', freq=spec_array_val[0]) )

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer loop, iterates over all qubits
        for acq_cha, (this_qubit, spec_pulse_amplitude_values) in enumerate(spec_pulse_amplitudes.items()):
            this_clock = f'{this_qubit}.01'

            frequency_values = spec_frequencies[this_qubit]
            number_of_freqs = len(frequency_values)

            schedule.add(
                    Reset(*qubits), ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            # The intermediate loop, iterates over all spec_amplitudes
            for ampl_indx, spec_pulse_amplitude in enumerate(spec_pulse_amplitude_values):

                #The inner for loop iterates over all frequency values in the frequency batch:
                for acq_index, spec_freq in enumerate(spec_frequencies[this_qubit]):
                    this_index = ampl_indx*number_of_freqs + acq_index
                    #reset the clock frequency for the qubit pulse
                    set_frequency = schedule.add(
                        SetClockFrequency(clock=this_clock, clock_freq_new=spec_freq),
                    )

                    #spectroscopy pulse
                    # print(f'{spec_pulse_durations=}')
                    # print(f'{this_clock=}')
                    spec_pulse = schedule.add(
                        long_square_pulse(
                            duration= spec_pulse_durations[this_qubit],
                            amp= spec_pulse_amplitude,
                            port= mw_pulse_ports[this_qubit],
                            clock=this_clock,
                        ),
                        label=f"spec_pulse_multidim_{this_qubit}_{this_index}", ref_op=set_frequency, ref_pt="end",
                    )
                    """  
                    spec_pulse = schedule.add(
                        SoftSquarePulse(
                            duration= spec_pulse_durations[this_qubit],
                            amp= spec_pulse_amplitudes[this_qubit],
                            port= mw_pulse_ports[this_qubit],
                            clock=this_clock,
                        ),
                        label=f"spec_pulse_{this_qubit}_{this_index}", ref_op=excitation_pulse, ref_pt="end",
                    )
                    """
                    if self.qubit_state == 0:
                        measure_function = Measure
                    elif self.qubit_state == 1:
                        measure_function = Measure_RO1
                    else:
                        raise ValueError(f'Invalid qubit state: {self.qubit_state}')

                    schedule.add(
                        measure_function(this_qubit, acq_index=this_index,bin_mode=BinMode.AVERAGE),
                        ref_op=spec_pulse,
                        ref_pt='end',
                        label=f'Measurement_{this_qubit}_{this_index}'
                    )

                    # update the relaxation for the next batch point
                    relaxation = schedule.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{this_index}")

        return schedule
