"""
Module containing a schedule class for T1 relaxation time measurement.
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from tergite_acl.lib.schedules.measurement_base import Measurement
import numpy as np

class T1(Measurement):

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
        """
        Generate a schedule for performing a T1 experiment measurement to find the relaxation time T_1 for multiple qubits.

        Schedule sequence
            Reset -> pi pulse -> Idel(tau) -> Measure
        
        Parameters
        ----------
        self
            Contains all qubit states.
        qubits
            The list of qubits on which to perform the experiment.
        delays
            Array of the sweeping delay times tau between the pi-pulse and the measurement for each qubit.
        repetitions
            The amount of times the Schedule will be repeated.
        
        Returns
        -------
        :
            An experiment schedule.
        """
        schedule = Schedule("multiplexed_T1",repetitions)

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Start")
        
        #First loop over every qubit with corresponding tau sweeping lists
        for this_qubit, times_val in delays.items():
            prev_relax = root_relaxation
            #Second loop over all tau delay values
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
