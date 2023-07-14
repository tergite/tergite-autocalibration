from quantify_scheduler.resources import ClockResource
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.operations.gate_library import Measure, Reset
from calibration_schedules.measurement_base import Measurement
import numpy as np

class XY_cross(Measurement):

    def __init__(self,transmons):
        super().__init__(transmons)

        self.static_kwargs = {
            'qubits': self.qubits,
            'mw_frequencies': self.attributes_dictionary('f01'),
            # 'mw_amplitudes': self.attributes_dictionary('mw_amp180'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
            # 'mw_pulse_durations': self.attributes_dictionary('mw_pulse_duration'),
        }


    def schedule_function(
            self,
            drive_qubit: str,
            qubits: list[str],
            mw_frequencies: dict[str,float],
            mw_amplitudes: dict[str,np.ndarray],
            mw_pulse_ports: dict[str,str],
            mw_pulse_durations: dict[str,np.ndarray],
            repetitions: int = 1024,
        ) -> Schedule:
        schedule = Schedule("XY_cross_talk",repetitions)

        for this_qubit, mw_f_val in mw_frequencies.items():
            print('sorry for spamming', this_qubit)
            schedule.add_resource(
                ClockResource( name=f'{this_qubit}.01', freq=mw_f_val)
            )

        schedule.add(Reset(*qubits), label="Reset")

        #On the outer loop we loop over all qubits
        for this_qubit in qubits:

            #On the middle loop we loop over all amplitudes for each qubit
            for amplitude in mw_amplitudes[this_qubit]:

                #On the inner loop we loop over the pulse durations
                for acq_index, mw_duration in enumerate(mw_pulse_durations[this_qubit]):

                    schedule.add(
                        DRAGPulse(
                            duration=mw_duration,
                            G_amp=amplitude,
                            D_amp=0,
                            port=mw_pulse_ports[drive_qubit], # This is where we change the input port
                            clock=f'{this_qubit}.01',
                            phase=0,
                        ),
                        label=f"drag_pulse_{this_qubit}_{acq_index}",
                    )

                    schedule.add( Measure(this_qubit, acq_index=acq_index), )

                    schedule.add(Reset(*qubits))

        return schedule
