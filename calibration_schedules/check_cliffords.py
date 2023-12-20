"""
Module containing a schedule class for clifford gate checks
"""
import numpy as np
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.gate_library import Measure, Reset, Rxy
from quantify_scheduler.schedules.schedule import Schedule
from calibration_schedules.measurement_base import Measurement
import utilities.clifford_elements_decomposition as cliffords
sequences = [[0],[13],[1,2],[6,7]] #temporary
# 0 -> 0 theta, 0 phi -> 0 ampl
# 13 -> -90 theta, 0 phi -> (0+1)/2 super pos ampl
# 1,2 -> 0 theta, 180 phi -> 0 ampl
# 6,7 -> 180 theta, 180 phi -> 1 ampl
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
            repetitions: int = 128,
        ) -> Schedule:

        sched = Schedule("multiplexed_RB",repetitions)
        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = sched.add(Reset(*qubits), label="Reset")
        # The first for loop iterates over all qubits:
        for acq_cha,this_qubit in enumerate(qubits):
            relaxation = sched.add(
                Reset(*qubits), label=f'Reset_{acq_cha}', ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            # The second for loop iterates over the random clifford sequence lengths
            for acq_index, sequence in enumerate(sequences):
                for sequence_index in sequence:
                    #print(f’{ sequence_index = }’)
                    physical_gates = cliffords.XY_decompositions[sequence_index]
                    for gate_index, gate_angles in physical_gates.items():
                        theta = gate_angles['theta']
                        phi = gate_angles['phi']
                        clifford_gate = sched.add(
                            Rxy(qubit=this_qubit,theta=theta,phi=phi)
                        )
                        # print(f’{ clifford_gate = }’)
                    sched.add(
                            Measure(this_qubit, acq_channel=acq_cha, acq_index=acq_index,bin_mode=BinMode.AVERAGE),
                            ref_op=clifford_gate,
                            ref_pt='end',
                            label=f'Measurement_{this_qubit}_{acq_index}'
                        )
            sched.add(Reset(this_qubit))
        return sched