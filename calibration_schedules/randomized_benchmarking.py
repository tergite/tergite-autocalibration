"""
Module containing a schedule class for randomized benchmarking measurement.
"""
import numpy as np
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.gate_library import Measure, Reset, Rxy, X
from quantify_scheduler.schedules.schedule import Schedule

from calibration_schedules.measurement_base import Measurement
import utilities.clifford_elements_decomposition as cliffords


class Randomized_Benchmarking(Measurement):
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
        number_of_cliffords: dict[str, np.ndarray],
        sequence_repetitions: dict[str, np.ndarray],
        repetitions: int = 1024,
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

        schedule = Schedule("multiplexed_randomized_benchmarking",repetitions)

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Start")

        # The first for loop iterates over all qubits:
        for this_qubit, clifford_sequence_lengths in number_of_cliffords.items():

            this_clifford_repetitions = sequence_repetitions[this_qubit]
            number_of_clifford_sequences = len(clifford_sequence_lengths)

            seed = 4
            all_cliffords = len(cliffords.XY_decompositions)
            rng = np.random.default_rng(seed)

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt='end'
            ) # To enforce parallelism we refer to the root relaxation

            for repetition_index, _ in enumerate(this_clifford_repetitions):
                # The inner for loop iterates over the random clifford sequence lengths
                for acq_index, this_number_of_cliffords in enumerate(clifford_sequence_lengths[:-2]):

                    this_index = number_of_clifford_sequences * repetition_index + acq_index
                    schedule.add(X(this_qubit))
                    random_sequence = rng.integers(all_cliffords, size=this_number_of_cliffords)

                    for sequence_index in random_sequence:
                        physical_gates = cliffords.XY_decompositions[sequence_index]
                        for gate_angles in physical_gates.values():
                            theta = gate_angles['theta']
                            phi = gate_angles['phi']
                            schedule.add(
                                Rxy(qubit=this_qubit,theta=theta,phi=phi)
                            )

                    recovery_index, recovery_XY_operations = cliffords.reversing_XY_matrix(random_sequence)

                    for gate_angles in recovery_XY_operations.values():
                        theta = gate_angles['theta']
                        phi = gate_angles['phi']
                        recovery_gate = schedule.add(
                            Rxy(qubit=this_qubit, theta=theta, phi=phi)
                        )

                    schedule.add(
                        Measure(this_qubit, acq_index=this_index,),
                        ref_op=recovery_gate,
                        ref_pt='end',
                    )

                    schedule.add(Reset(this_qubit))


                # 0 calibration point
                schedule.add(Measure( this_qubit, acq_index=this_index + 1))
                schedule.add(Reset(this_qubit))

                # 1 calibration point
                schedule.add(X(this_qubit))
                schedule.add( Measure( this_qubit, acq_index=this_index + 2))
                schedule.add(Reset(this_qubit))

        return schedule
