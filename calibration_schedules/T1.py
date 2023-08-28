from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from calibration_schedules.measurement_base import Measurement
import numpy as np

class T1_BATCHED(Measurement):

    def __init__(self,transmons,qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

        self.static_kwargs = {
            'qubits': self.qubits,
        }

    def schedule_function(
        self,
        qubits: list[str],
        delays: dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:
        schedule = Schedule("multiplexed_T1",repetitions)
        root_relaxation = schedule.add(Reset(*qubits), label="Start")
        
        for this_qubit, times_val in delays.items():
            prev_relax = root_relaxation
            for acq_index, tau in enumerate(times_val):
                relaxation=schedule.add(Reset(this_qubit), ref_op=prev_relax, label=f"Reset {this_qubit} {acq_index}")
                schedule.add(X(this_qubit), label=f"pi {this_qubit} {acq_index}")
                schedule.add(
                    Measure(this_qubit, acq_index=acq_index, bin_mode=BinMode.AVERAGE),
                    ref_pt="start",
                    rel_time=tau,
                    label=f"Measurement {this_qubit} {acq_index}",
                )
                prev_relax=relaxation
        return schedule
