from quantify_scheduler.operations.gate_library import Reset, X, Rxy, Measure
from quantify_scheduler.operations.pulse_library import SquarePulse, SetClockFrequency
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.schedules.schedule import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.resources import ClockResource
from calibration_schedules.measurement_base import Measurement
from quantify_scheduler.enums import BinMode
from utilities.extended_transmon_element import Measure_RO_Opt
import numpy as np

class Single_Shots_RO(Measurement):

    def __init__(self,transmons,qubit_state:int=0):
        super().__init__(transmons)

        self.transmons = transmons
        self.static_kwargs = {
            'qubits': self.qubits,
            'freqs_12': self.attributes_dictionary('f12'),
            'mw_ef_amp180s': self.attributes_dictionary('ef_amp180'),
            'mw_pulse_durations': self.attributes_dictionary('duration'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
        }


    def schedule_function(
            self,
            qubits : list[str],
            freqs_12:  dict[str,float],
            mw_ef_amp180s: dict[str,float],
            mw_pulse_durations: dict[str,float],
            mw_pulse_ports: dict[str,str],
            qubit_states: dict[str,np.ndarray],
            repetitions: int = 1
        ) -> Schedule:
        schedule = Schedule("State_discrimination_schedule", repetitions)
        print(f'{ repetitions = }')

        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer for-loop iterates over all qubits:
        for this_qubit, levels in qubit_states.items():

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            # The inner for-loop iterates over all qubit levels:
            for level_index, state_level in enumerate(levels):

                if state_level == 0:
                    # Not really necessary to use Rxy(0,0) we can just pass
                    schedule.add(
                        Rxy(theta=0, phi=0, qubit=this_qubit),
                    )
                elif state_level == 1:
                    schedule.add(X(this_qubit))

                elif state_level == 2:
                    pass
                    # schedule.add(X(qubit = this_qubit))
                    # schedule.add(
                    #     #TODO DRAG optimize for 1 <-> 2
                    #     DRAGPulse(
                    #         duration=mw_pulse_durations[this_qubit],
                    #         G_amp=mw_ef_amp180s[this_qubit],
                    #         D_amp=0,
                    #         port=mw_pulse_ports[this_qubit],
                    #         clock=mw_clocks_12[this_qubit],
                    #         phase=0,
                    #     ),
                    # )
                else:
                    raise ValueError('State Input Error')

                schedule.add(
                    Measure_RO_Opt(
                    this_qubit,
                    acq_index=level_index,
                    bin_mode=BinMode.AVERAGE
                    ),
                )
                # update the root operation
                schedule.add(Reset(this_qubit))

        return schedule
