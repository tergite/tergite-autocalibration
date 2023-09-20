from quantify_scheduler.operations.gate_library import Reset, X, Rxy
from quantify_scheduler.operations.pulse_library import SquarePulse, SetClockFrequency
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.schedules.schedule import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.resources import ClockResource
from calibration_schedules.measurement_base import Measurement
from quantify_scheduler.enums import BinMode
from utilities.extended_transmon_element import Measure_RO_Opt

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
            repetitions: int = 1,
            qubit_states: dict[str,int]
        ) -> Schedule:
        schedule = Schedule("State_discrimination_schedule", repetitions)
        print(f'{ repetitions = }')

        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer for-loop iterates over all qubits:
        for acq_cha, (this_qubit, levels) in enumerate(state_levels.items()):

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            # The inner for-loop iterates over all qubit levels:
            for rng_index, state_level in enumerate(levels):
                # require an integer
                # state_level = int(state_level+1e-2)
                assert(type(state_level)==int)

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
                    acq_index=rng_index,
                    bin_mode=BinMode.APPEND
                    ),
                )
                # update the root operation
                schedule.add(Reset(this_qubit))

        return schedule
