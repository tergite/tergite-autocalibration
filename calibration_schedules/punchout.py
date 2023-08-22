from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.resources import ClockResource
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import SquarePulse, SetClockFrequency
from quantify_scheduler.operations.gate_library import Reset
from calibration_schedules.measurement_base import Measurement
import numpy as np


class Punchout(Measurement):

    def __init__(self,transmons):
        super().__init__(transmons)
        self.transmons = transmons

        self.static_kwargs = {
            'qubits': self.qubits,
            'pulse_durations': self.attributes_dictionary('pulse_duration'),
            'acquisition_delays': self.attributes_dictionary('acq_delay'),
            'integration_times': self.attributes_dictionary('integration_time'),
            'ports': self.attributes_dictionary('readout_port'),
        }


    def schedule_function(
            self,
            qubits: list[str],
            pulse_durations: dict[str,float],
            acquisition_delays: dict[str,float],
            integration_times: dict[str,float],
            ports: dict[str,str],
            ro_frequencies: dict[str,np.ndarray],
            ro_amplitudes: dict[str,np.ndarray],
            repetitions: int = 1024,
        ) -> Schedule:
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
