"""
Module containing a schedule class for randomized benchmarking measurement.
"""
import numpy as np
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X, CZ
from quantify_scheduler.operations.pulse_library import ResetClockPhase, SoftSquarePulse, IdlePulse

from quantify_scheduler.schedules.schedule import Schedule

from tergite_acl.lib.measurement_base import Measurement
import tergite_acl.utils.clifford_elements_decomposition as cliffords
from tergite_acl.utils.extended_transmon_element import ExtendedTransmon
from tergite_acl.utils.extended_coupler_edge import CompositeSquareEdge
from quantify_scheduler.resources import ClockResource

# Compile randomized benchmarking gate sequence
from tergite_acl.utils.clifford_module.randomized_benchmarking import *
from tergite_acl.utils.clifford_module.cliffords_decomposition import (decompose_clifford_seq,)
from tergite_acl.utils.clifford_module.from_list import (add_single_qubit_gates_to_schedule,add_two_qubit_gates_to_schedule,)

class Randomized_Benchmarking(Measurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

    def schedule_function(
        self,
        seed: int,
        number_of_cliffords: dict[str, np.ndarray],
        repetitions: int = 1024,
        ) -> Schedule:
        """
        Generate a schedule for performing a randomized benchmarking test using Clifford gates.
        The goal is to get a measure of the total error of the calibrated qubits.

        Schedule sequence
            Reset -> Apply Clifford operations-> Apply inverse of all Clifford operations -> Measure

        Parameters
        ----------
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

        qubits = self.transmons.keys()

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Start")

        # The first for loop iterates over all qubits:
        for this_qubit, clifford_sequence_lengths in number_of_cliffords.items():

            all_cliffords = len(cliffords.XY_decompositions)
            rng = np.random.default_rng(seed)

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt='end'
            ) # To enforce parallelism we refer to the root relaxation

            # The inner for loop iterates over the random clifford sequence lengths
            for acq_index, this_number_of_cliffords in enumerate(clifford_sequence_lengths[:-2]):

                #schedule.add(X(this_qubit))
                # schedule.add(X(this_qubit))
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
                    Measure(this_qubit, acq_index=acq_index,),
                    ref_op=recovery_gate,
                    ref_pt='end',
                )

                schedule.add(Reset(this_qubit))


            # 0 calibration point
            schedule.add(Reset(this_qubit))
            schedule.add(Reset(this_qubit))
            schedule.add(Measure( this_qubit, acq_index=acq_index + 1))
            schedule.add(Reset(this_qubit))

            # 1 calibration point
            schedule.add(Reset(this_qubit))
            schedule.add(Reset(this_qubit))
            schedule.add(X(this_qubit))
            schedule.add(Measure( this_qubit, acq_index=acq_index + 2))
            schedule.add(Reset(this_qubit))

        return schedule


class TQG_Randomized_Benchmarking(Measurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon],couplers: dict[str, CompositeSquareEdge], qubit_state: int = 0):
        super().__init__(transmons)
        self.transmons = transmons
        self.qubit_state = qubit_state
        self.couplers = couplers

    def schedule_function(
        self,
        seed: int,
        number_of_cliffords: dict[str, np.ndarray],
        interleaving_clifford_id: int = None,
        apply_inverse_gate: bool =True,
        repetitions: int = 1024,
        ) -> Schedule:
        """
        Generate a schedule for performing a randomized benchmarking test using Clifford gates.
        The goal is to get a measure of the total error of the calibrated qubits.

        Schedule sequence
            Reset -> Apply Clifford operations-> Apply inverse of all Clifford operations -> Measure

        Parameters
        ----------
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
        if interleaving_clifford_id is None:
            name = "tqg_randomized_benchmarking"
        else:
            name = "tqg_randomized_benchmarking_interleaved"
        schedule = Schedule(name,repetitions)

        qubits = list(self.transmons.keys())
        coupler_names = self.couplers.keys()
        coupled_qubits = [coupler.split('_') for coupler in coupler_names]

        for index, this_coupler in enumerate(coupler_names):
            schedule.add_resource(
                ClockResource(name=f'{this_coupler}.cz', freq=4.4e9-self.couplers[this_coupler].clock_freqs.cz_freq())
            )

        print(self.couplers[this_coupler].clock_freqs.cz_freq())
        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Start")

        # The first for loop iterates over all qubits:
        # for this_qubit, clifford_sequence_lengths in number_of_cliffords.items():
        clifford_sequence_lengths = list(number_of_cliffords.values())[0]

        # all_cliffords = len(cliffords.XY_decompositions)
        # rng = np.random.default_rng(seed)


        # The inner for loop iterates over the random clifford sequence lengths
        for acq_index, this_number_of_cliffords in enumerate(clifford_sequence_lengths[:-2]):

            # schedule.add(X(this_qubit))
            # random_sequence = rng.integers(all_cliffords, size=this_number_of_cliffords)

            start = schedule.add(IdlePulse(4e-9))

            # for clifford_index, sequence_index in enumerate(random_sequence):
            # n_cl = 1
            index = 0
            # seed = 42
            # interleaving_clifford_id = 4386 #CZ
            # interleaving_clifford_id = None
            # apply_inverse_gate = False
            # qubit_names_list = ['Q1', 'Q2']
            clifford_seq = randomized_benchmarking_sequence(
                n_cl=this_number_of_cliffords,
                meas_basis_index=index,
                seed=seed,
                interleaving_clifford_id=interleaving_clifford_id,
                apply_inverse_gate=apply_inverse_gate,
                number_of_qubits=2,
            )
            physical_gates = decompose_clifford_seq(clifford_seq, qubits)

            separation_time = 300e-9
            # schedule = Schedule('rb_sequence_generation')
            reset = schedule.add(Reset(*qubits))

            add_two_qubit_gates_to_schedule(
                            schedule, physical_gates, ref_op=reset, separation_time=separation_time
                        )

            buffer = schedule.add(IdlePulse(4e-9))                                                          
            for this_qubit in qubits:
                schedule.add(
                    Measure(this_qubit, acq_index=acq_index),
                    ref_op=buffer,
                    ref_pt='end',
                )           
                end = schedule.add(Reset(this_qubit))

        for this_qubit in qubits:
            # 0 calibration point
            schedule.add(Reset(this_qubit), ref_op=end, ref_pt='end')
            schedule.add(Measure( this_qubit, acq_index=acq_index + 1))

            # 1 calibration point
            schedule.add(Reset(this_qubit))
            schedule.add(X(this_qubit))
            schedule.add(Measure( this_qubit, acq_index=acq_index + 2))
            schedule.add(Reset(this_qubit))

        return schedule

class Cross_Entropy_Randomized_Benchmarking_Backup(Measurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon],couplers: dict[str, CompositeSquareEdge], qubit_state: int = 0):
        super().__init__(transmons)
        self.transmons = transmons
        self.qubit_state = qubit_state
        self.couplers = couplers

    def schedule_function(
        self,
        seed: int,
        number_of_cliffords: dict[str, np.ndarray],
        repetitions: int = 1024,
        ) -> Schedule:
        """
        Generate a schedule for performing a randomized benchmarking test using Clifford gates.
        The goal is to get a measure of the total error of the calibrated qubits.

        Schedule sequence
            Reset -> Apply Clifford operations-> Apply inverse of all Clifford operations -> Measure

        Parameters
        ----------
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

        schedule = Schedule("cross_entropy_randomized_benchmarking",repetitions)

        qubits = self.transmons.keys()
        coupler_names = self.couplers.keys()
        coupled_qubits = [coupler.split('_') for coupler in coupler_names]

        for index, this_coupler in enumerate(coupler_names):
            schedule.add_resource(
                ClockResource(name=f'{this_coupler}.cz', freq=4.4e9-self.couplers[this_coupler].clock_freqs.cz_freq())
            )

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Start")

        # The first for loop iterates over all qubits:
        # for this_qubit, clifford_sequence_lengths in number_of_cliffords.items():
        clifford_sequence_lengths = list(number_of_cliffords.values())[0]

        all_cliffords = len(cliffords.XY_decompositions)
        rng = np.random.default_rng(seed)

        # The inner for loop iterates over the random clifford sequence lengths
        for acq_index, this_number_of_cliffords in enumerate(clifford_sequence_lengths[:-2]):

            # schedule.add(X(this_qubit))
            random_sequence = rng.integers(all_cliffords, size=this_number_of_cliffords)

            start = schedule.add(IdlePulse(4e-9))

            for clifford_index, sequence_index in enumerate(random_sequence):
                for this_qubit in qubits:
                    physical_gates = cliffords.XY_decompositions[sequence_index]
                    for gate_index, gate_angles in enumerate(physical_gates.values()):
                            theta = gate_angles['theta']
                            phi = gate_angles['phi']
                            if gate_index == 0:
                                last_gate = schedule.add(
                                    Rxy(qubit=this_qubit,theta=theta,phi=phi),
                                    ref_op=start,ref_pt='end')
                            else:
                                last_gate = schedule.add(
                                    Rxy(qubit=this_qubit,theta=theta,phi=phi)
                            )
                if clifford_index < this_number_of_cliffords:
                    for this_coupler in coupled_qubits:
                        start = schedule.add(CZ(this_coupler[0],this_coupler[1]), ref_op=last_gate, ref_pt='end')

            recovery_index, recovery_XY_operations = cliffords.reversing_XY_matrix(random_sequence)
            for this_qubit in qubits:
                for gate_index, gate_angles in enumerate(recovery_XY_operations.values()):
                    theta = gate_angles['theta']
                    phi = gate_angles['phi']
                    if gate_index == 0:
                        last_gate = schedule.add(
                            Rxy(qubit=this_qubit,theta=theta,phi=phi),
                            ref_op=start,ref_pt='end')
                    else:
                        last_gate = schedule.add(
                            Rxy(qubit=this_qubit,theta=theta,phi=phi)
                    )  
                                                                                

                schedule.add(
                    Measure(this_qubit, acq_index=acq_index),
                    ref_op=last_gate,
                    ref_pt='end',
                )           
                end = schedule.add(Reset(this_qubit))

        for this_qubit in qubits:
            # 0 calibration point
            schedule.add(Reset(this_qubit), ref_op=end, ref_pt='end')
            schedule.add(Measure( this_qubit, acq_index=acq_index + 1))

            # 1 calibration point
            schedule.add(Reset(this_qubit))
            schedule.add(X(this_qubit))
            schedule.add(Measure( this_qubit, acq_index=acq_index + 2))

        return schedule
