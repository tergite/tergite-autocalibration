from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from measurements_base import Measurement_base


class T1_BATCHED(Measurement_base):

    def __init__(self,transmons,connections,qubit_state:int=0):
        super().__init__(transmons,connections)
        self.experiment_parameters = 'delay'
        self.gettable_batched = True
        self.qubit_state = qubit_state
        self.static_kwargs = {
            'qubits': self.qubits,
        }

    def settables_dictionary(self):
        parameters = self.experiment_parameters
        manual_parameter = 'delay'
        assert( manual_parameter in self.experiment_parameters )
        mp_data = {
            manual_parameter : {
                'name': manual_parameter,
                'initial_value': 4e-9,
                'unit': 's',
                'batched': True
            }
        }
        return self._settables_dictionary(parameters, isBatched=self.gettable_batched, mp_data=mp_data)

    def setpoints_array(self):
        return self._setpoints_1d_array()


    def schedule_function(
        self,
        qubits: list[str],
        repetitions: int = 1024,
        **delays
    ):
        schedule = Schedule("multiplexed_T1",repetitions)
        root_relaxation = schedule.add(Reset(*qubits), label="Start")
        
        for acq_cha, (times_key, times_val) in enumerate(delays.items()):
            this_qubit = qubits[acq_cha]
            prev_relax = root_relaxation
            for i, tau in enumerate(times_val):
                relaxation=schedule.add(Reset(this_qubit), ref_op=prev_relax, label=f"Reset {acq_cha} {i}")
                schedule.add(X(this_qubit), label=f"pi {acq_cha} {i}")
                schedule.add(
                    Measure(this_qubit,acq_channel=acq_cha, acq_index=i),
                    ref_pt="start",
                    rel_time=tau,
                    label=f"Measurement {acq_cha} {i}",
                )
                prev_relax=relaxation
        return schedule

