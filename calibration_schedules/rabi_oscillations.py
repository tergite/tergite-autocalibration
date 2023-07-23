from quantify_scheduler.resources import ClockResource
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from calibration_schedules.measurement_base import Measurement
import numpy as np

# from transmon_element import Measure_1

class Rabi_Oscillations(Measurement):

    def __init__(self,transmons,qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

        self.static_kwargs = {
            'qubits': self.qubits,
            'mw_frequencies': self.attributes_dictionary('f01'),
            'mw_pulse_durations': self.attributes_dictionary('duration'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
        }


    def schedule_function(
        self,
        qubits: list[str],
        mw_frequencies: dict[str,float],
        mw_pulse_durations: dict[str,float],
        mw_pulse_ports: dict[str,str],
        mw_amplitudes: dict[str, np.ndarray],
        repetitions: int = 1024,
        ) -> Schedule:

        if self.qubit_state == 0:
            schedule_title = "multiplexed_rabi_01"
            measure_function = Measure
        # elif self.qubit_state == 1:
        #     schedule_title = "multiplexed_rabi_12_BATCHED"
        #     measure_function = Measure_1
        else:
            raise ValueError(f'Invalid qubit state: {self.qubit_state}')

        sched = Schedule(schedule_title,repetitions)
        print(f'{mw_frequencies=}')
        print(f'{mw_pulse_durations=}')

        for this_qubit, mw_f_val in mw_frequencies.items():
            sched.add_resource(
                ClockResource( name=f'{this_qubit}.01', freq=mw_f_val)
            )

        # for this_qubit, mw_f_val in mw_frequencies_12.items():
        #     sched.add_resource(
        #         ClockResource( name=f'{this_qubit}.12', freq=mw_f_val)
        #     )

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = sched.add(Reset(*qubits), label="Reset")

        for this_qubit, mw_amp_array_val in mw_amplitudes.items():
            if self.qubit_state == 0:
                this_clock = f'{this_qubit}.01'
            # elif self.qubit_state == 1:
            #     this_clock = mw_clocks_12[this_qubit]
            else:
                raise ValueError(f'Invalid qubit state: {self.qubit_state}')

            # The second for loop iterates over all frequency values in the frequency batch:
            relaxation = root_relaxation #To enforce parallelism we refer to the root relaxation
            for acq_index, mw_amplitude in enumerate(mw_amp_array_val):
                if self.qubit_state == 1:
                    relaxation = sched.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                mw_pulse = sched.add(
                    DRAGPulse(
                        duration=mw_pulse_durations[this_qubit],
                        G_amp=mw_amplitude,
                        D_amp=0,
                        port=mw_pulse_ports[this_qubit],
                        clock=this_clock,
                        phase=0,
                    ),
                    label=f"rabi_pulse_{this_qubit}_{acq_index}", ref_op=relaxation, ref_pt="end",
                )


                sched.add(
                    measure_function(this_qubit, acq_index=acq_index, bin_mode=BinMode.AVERAGE),
                    label=f'Measurement_{this_qubit}_{acq_index}',
                    ref_op=mw_pulse,
                    ref_pt="end",
                )

                # update the relaxation for the next batch point
                relaxation = sched.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{acq_index}")

        return sched
