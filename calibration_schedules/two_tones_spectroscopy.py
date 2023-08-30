from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from quantify_scheduler.operations.pulse_library import SetClockFrequency, SoftSquarePulse
from quantify_scheduler.resources import ClockResource
from quantify_scheduler.schedules.schedule import Schedule
from utilities.extended_transmon_element import Measure_RO1
import numpy as np

from calibration_schedules.measurement_base import Measurement

class Two_Tones_Spectroscopy(Measurement):

    def __init__(self,transmons,qubit_state:int=0):
        super().__init__(transmons)

        self.qubit_state = qubit_state
        self.transmons = transmons

        self.static_kwargs = {
            'qubits': self.qubits,
            'mw_pulse_durations': self.attributes_dictionary('duration'),
            'mw_pulse_amplitudes': self.attributes_dictionary('amp180'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
        }


    def schedule_function(
        self,
        qubits: list[str],
        mw_pulse_durations: dict[str,float],
        mw_pulse_amplitudes: dict[str,float],
        mw_pulse_ports: dict[str,str],
        mw_frequencies: dict[str,np.ndarray],

        repetitions: int = 512,
        ) -> Schedule:

        # if port_out is None: port_out = port
        schedule = Schedule("multiplexed_qubit_spec",repetitions)
        # Initialize the clock for each qubit
        for this_qubit, spec_array_val in mw_frequencies.items():
            if self.qubit_state == 0:
                this_clock = f'{this_qubit}.01'
            elif self.qubit_state == 1:
                this_clock = f'{this_qubit}.12'
            else:
                raise ValueError(f'Invalid qubit state: {self.qubit_state}')
            #print(f'{this_clock = }')
            #print(f'{spec_array_val[0] = }')
            schedule.add_resource(
                ClockResource(name=this_clock, freq=spec_array_val[0]),
            )

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The first for loop iterates over all qubits:
        for this_qubit, spec_array_val in mw_frequencies.items():
            if self.qubit_state == 0:
                this_clock = f'{this_qubit}.01'
            elif self.qubit_state == 1:
                this_clock = f'{this_qubit}.12'
            else:
                raise ValueError(f'Invalid qubit state: {self.qubit_state}')

            # The second for loop iterates over all frequency values in the frequency batch:
            relaxation = root_relaxation #To enforce parallelism we refer to the root relaxation
            for acq_index, spec_pulse_frequency in enumerate(spec_array_val):
                #reset the clock frequency for the qubit pulse
                set_frequency = schedule.add(
                    SetClockFrequency(clock=this_clock, clock_freq_new=spec_pulse_frequency),
                    label=f"set_freq_{this_qubit}_{acq_index}",
                    ref_op=relaxation, ref_pt='end'
                )

                if self.qubit_state == 0:
                    excitation_pulse = set_frequency
                elif self.qubit_state == 1:
                    excitation_pulse = schedule.add(X(this_qubit), ref_op=set_frequency, ref_pt='end')
                else:
                    raise ValueError(f'Invalid qubit state: {self.qubit_state}')

                #spectroscopy pulse
                print(f'{mw_pulse_durations=}')
                print(f'{this_clock=}')
                spec_pulse = schedule.add(
                    SoftSquarePulse(
                        duration= mw_pulse_durations[this_qubit],
                        amp= mw_pulse_amplitudes[this_qubit],
                        port= mw_pulse_ports[this_qubit],
                        clock=this_clock,
                    ),
                    label=f"spec_pulse_{this_qubit}_{acq_index}", ref_op=excitation_pulse, ref_pt="end",
                )

                if self.qubit_state == 0:
                    measure_function = Measure
                elif self.qubit_state == 1:
                    measure_function = Measure_RO1
                else:
                    raise ValueError(f'Invalid qubit state: {self.qubit_state}')

                schedule.add(
                    measure_function(this_qubit, acq_index=acq_index,bin_mode=BinMode.AVERAGE),
                    ref_op=spec_pulse,
                    ref_pt='end',
                    label=f'Measurement_{this_qubit}_{acq_index}'
                )

                # update the relaxation for the next batch point
                relaxation = schedule.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{acq_index}")

        return schedule
