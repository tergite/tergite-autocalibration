"""
Module containing a schedule class for randomized benchmarking measurement.
"""
import numpy as np
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.gate_library import Measure, Reset, Rxy
from quantify_scheduler.schedules.schedule import Schedule

from measurements_base import Measurement_base
import randomized_benchmarking.clifford_elements_decomposition as cliffords


class Randomized_Benchmarking_BATCHED(Measurement_base):
    def __init__(self,transmons,connections,qubit_state:int=0):
        super().__init__(transmons,connections)
        self.experiment_parameters = ['number_of_cliffords']
        self.gettable_batched = True
        self.qubit_state = qubit_state
        self.static_kwargs = {
            'qubits': self.qubits,
        }

    def settables_dictionary(self):
        manual_parameter = 'number_of_cliffords'
        parameters = self.experiment_parameters
        assert( manual_parameter in self.experiment_parameters )
        mp_data = {
            manual_parameter : {
                'name': manual_parameter,
                'initial_value': 2,
                'unit': '-',
                'batched': True
            }
        }
        return self._settables_dictionary(parameters, isBatched=self.gettable_batched, mp_data=mp_data)

    def setpoints_array(self):
        return self._setpoints_1d_array()

    def schedule_function(
            self, #Note, this is not used in the schedule
            qubits: list[str],
            repetitions: int = 128,
            **number_of_cliffords_operations,
        ) -> Schedule:
        """
        Generate a schedule for performing a randomized benchmarking test using Clifford gates.
        The goal is to get a measure of the total error of the calibrated qubits.

        Schedule sequence
            Reset -> Apply Clifford operations-> Apply inverse of all Clifford operations -> Measure
        
        Parameters
        ----------
        self
            Contains all qubit states.
        qubits
            The list of qubits on which to perform the experiment.
        repetitions
            The amount of times the Schedule will be repeated.
        **number_of_cliffords_operations
            The number of random Clifford operations applied and then inverted on each qubit state.
            This parameter is swept over.
        
        Returns
        -------
        :
            An experiment schedule.
        """

        # if port_out is None: port_out = port
        sched = Schedule("multiplexed_RB",repetitions)
        # Initialize the clock for each qubit
        for rb_key in number_of_cliffords_operations.keys():
            this_qubit = [qubit for qubit in qubits if qubit in rb_key][0]


        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = sched.add(Reset(*qubits), label="Reset")

        # The first for loop iterates over all qubits:
        for acq_cha, (rb_key, clifford_sequence_lengths) in enumerate(number_of_cliffords_operations.items()):
            this_qubit = [qubit for qubit in qubits if qubit in rb_key][0]
            print(f'{ this_qubit = }')

            relaxation = sched.add(
                Reset(*qubits), label=f'Reset_{acq_cha}', ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            # The second for loop iterates over the random clifford sequence lengths
            for acq_index, number_of_cliffords in enumerate(clifford_sequence_lengths):
                print( )
                print(f'{ number_of_cliffords = }')
                seed = 1
                all_cliffords = len(cliffords.XY_decompositions)
                # print(f'{ all_cliffords = }')
                rng = np.random.default_rng(seed)
                random_sequence = rng.integers(all_cliffords, size=number_of_cliffords)

                print(f'{ random_sequence = }')
                for sequence_index in random_sequence:
                    print(f'{ sequence_index = }')
                    physical_gates = cliffords.XY_decompositions[sequence_index]
                    for gate_index, gate_angles in physical_gates.items():
                        theta = gate_angles['theta']
                        phi = gate_angles['phi']
                        clifford_gate = sched.add(
                            Rxy(qubit=this_qubit,theta=theta,phi=phi)
                        )
                        # print(f'{ clifford_gate = }')

                recovery_index, recovery_XY_operations = cliffords.reversing_XY_matrix(random_sequence)
                print(f'{ recovery_XY_operations = }')
                for gate_index, gate_angles in recovery_XY_operations.items():
                    theta = gate_angles['theta']
                    phi = gate_angles['phi']
                    recovery_gate = sched.add(
                        Rxy(qubit=this_qubit,theta=theta,phi=phi)
                    )

                sched.add(
                        Measure(this_qubit, acq_channel=acq_cha, acq_index=acq_index,bin_mode=BinMode.AVERAGE),
                        ref_op=recovery_gate,
                        ref_pt='end',
                        label=f'Measurement_{this_qubit}_{acq_index}'
                    )

                all_indexes = np.append(random_sequence, recovery_index)
                print(f'{ cliffords.is_sequence_identity(all_indexes) = }')

                sched.add(Reset(this_qubit))

        return sched
