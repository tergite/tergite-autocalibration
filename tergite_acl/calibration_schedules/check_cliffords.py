"""
Module containing a schedule class for clifford gate checks
"""
import numpy as np
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.gate_library import Measure, Reset, Rxy, X
from quantify_scheduler.schedules.schedule import Schedule
from tergite_acl.calibration_schedules.measurement_base import Measurement
import tergite_acl.utilities.clifford_elements_decomposition as cliffords


class Check_Cliffords(Measurement):
    def __init__(self, transmons, qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons
        self.static_kwargs = {
            'qubits': self.qubits,
        }
    def schedule_function(
            self,
            qubits: list[str],
            clifford_indices: dict[str, np.ndarray],
            repetitions: int = 1024,
        ) -> Schedule:

        schedule = Schedule("multiplexed_cliffords_check", repetitions)
        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")
        # The first for loop iterates over all qubits:
        for acq_cha,this_qubit in enumerate(qubits):
            # The second for loop iterates over the random clifford sequence lengths
            for clifford_index in clifford_indices:
                if clifford_index == 0:
                    schedule.add(
                        Measure(this_qubit, acq_index=clifford_index,bin_mode=BinMode.AVERAGE),
                        ref_op=root_relaxation,
                        ref_pt='end',
                        label=f'Measurement_{this_qubit}_{clifford_index}'
                    )
                elif clifford_index == 1:
                    schedule.add(X(this_qubit))
                    schedule.add(
                        Measure(this_qubit, acq_index=clifford_index,bin_mode=BinMode.AVERAGE),
                        label=f'Measurement_{this_qubit}_{clifford_index}'
                    )
                else:
                    physical_gate = cliffords.XY_decompositions[clifford_index-2]
                    #for gate_index, gate_angles in physical_gates.items():
                    clifford_gate = schedule.add(
                        Rxy(qubit=this_qubit,theta=physical_gate['theta'],phi=physical_gate['phi'])
                    )
                        # print(f’{ clifford_gate = }’)
                    schedule.add(
                        Measure(this_qubit, acq_channel=acq_cha, acq_index=clifford_index,bin_mode=BinMode.AVERAGE),
                        ref_op=clifford_gate,
                        ref_pt='end',
                        label=f'Measurement_{this_qubit}_{clifford_index}'
                    )
                
                schedule.add(Reset(this_qubit))
        return schedule