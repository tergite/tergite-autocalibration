# This code is part of Tergite
#
# (C) Copyright Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np
from numpy.typing import NDArray
from quantify_scheduler import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.control_flow_library import Loop
from quantify_scheduler.operations.gate_library import Reset, X
from quantify_scheduler.operations.pulse_library import IdlePulse
from quantify_scheduler.resources import ClockResource

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.extended_coupler_edge import (
    ExtendedCompositeSquareEdge,
)
from tergite_autocalibration.utils.extended_gates import Rxy_12, Measure_RO_3state_Opt
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon
from tergite_autocalibration.utils.logger.tac_logger import logger



# TODO: REMOVE THE DEPENDENCY OF THIS PACKAGE.
try:
    #from superconducting_qubit_tools.clifford_module.randomized_benchmarking import (
    #    randomized_benchmarking_sequence,
    #)
    from superconducting_qubit_tools.clifford_module.cliffords_decomposition import (
        decompose_clifford_seq,
    )
    from superconducting_qubit_tools.utils.clifford_module.from_list import (
        add_two_qubit_gates_to_schedule,
    )
except ImportError:
    logger.warning(
        "Could not find package: superconducting-qubit-tools.",
        "This is a proprietary licenced software.",
        "Please make sure that you are having a correct licence and install the dependency",
    )
    


class TQGRandomizedBenchmarkingSSRO(BaseMeasurement):
    def __init__(
        self,
        transmons: dict[str, ExtendedTransmon],
        couplers: dict[str, ExtendedCompositeSquareEdge],
        qubit_state: int = 0,
    ):
        super().__init__(transmons)
        self.transmons = transmons
        self.couplers = couplers
        self.qubit_state = qubit_state
    
    def calculate_net_clifford(
        self,
        rb_clifford_indices: NDArray[np.uint32],
        Clifford: type[CliffordBase] = SingleQubitCliffords,
    ) -> CliffordBase:
        """
        Calculate the net-clifford from a list of cliffords indices.

        Parameters
        ----------
        rb_clifford_indices
        list or array of integers specifying the cliffords.
        Clifford
        Clifford object used to determine what inversion technique
        to use and what indices are valid.
        Valid choices are `SingleQubitCliffords` and `TwoQubitCliffords`.

        Returns
        -------
        :
            A `Clifford` object containing the net-clifford.
            The Clifford index is contained in the Clifford.idx attribute.

        Notes
        -----
        The order corresponds to the order in a pulse sequence but is the reverse of
        what it would be in a chained dot product.
        In order to benchmark specific gates (and not cliffords), e.g. CZ but not as a
        member of the CNOT-like set of gates, or an identity with
        the same duration as the CZ we use, by convention, when specifying
        the interleaved gate, the index of the corresponding clifford + 100000.
        This is to keep it readable and bigger than the 11520 elements of the
        Two-qubit Clifford group corresponding clifford.

        """

        # Calculate the net clifford
        net_clifford = Clifford(np.uint32(0))  # assumes element 0 is the Identity
        for idx in rb_clifford_indices:
            assert idx > -1, f"Specify the index as {100_000 + abs(idx)}"
            cliff = Clifford(idx % 100_000)
            # order of operators applied in is right to left, therefore
            # the new operator is applied on the left side.
            net_clifford = cliff * net_clifford
        return net_clifford
    
    def calculate_recovery_clifford(
        self,
        cl_in: np.uint32,
        desired_cl: np.uint32,
        Clifford: type[CliffordBase] = SingleQubitCliffords,
    ) -> np.uint32:
        """
        Extracts the clifford that has to be applied to cl_in to make the net
        operation correspond to desired_cl from the clifford hashtable.

        This operation should perform the inverse of :code:`calculate_net_clifford`.

        Parameters
        ----------
        cl_in
        An integer value depicting the index of the input Clifford.
        desired_cl
        An integer value depicting the index of the desired Clifford.
        The desired Cliffords are specific Clifford gates of I,X,Y,Z,H.
        These five gates have their respective indices as 0,3,6,9,12.
        The desired_cl value is always a value within the above 5 integers.
        Clifford
        Clifford object used to determine what inversion technique to use
        and what indices are valid.
        Valid choices are `SingleQubitCliffords` and `TwoQubitCliffords`.

        Returns
        -------
        :
            The index of the Clifford to be added to get the desired Clifford.

        """

        clifford_in = Clifford(cl_in)
        desired_clifford = Clifford(desired_cl)
        output_index = (desired_clifford * clifford_in.get_inverse()).idx

        return output_index

    def randomized_benchmarking_sequence(
        self,
        n_cl: np.uint32,
        meas_basis_index: np.uint32 | int = 0,
        number_of_qubits: int = 1,
        max_clifford_idx: int = 11520,
        interleaving_clifford_id: int | None = None,
        apply_inverse_gate: bool = True,
        seed: np.uint32 | None = None,
    ) -> NDArray[np.uint32]:
        """
        Generates a randomized benchmarking sequence for the one or two qubit
        clifford group.

        Parameters
        ----------
        n_cl
        A integer specifying the number of Cliffords
        meas_basis_index
            An integer specifying the idx of the clifford that performs the
            rotation to the desired measurement basis
            By default, the measurement is done in the Z basis
        number_of_qubits
            Integer value used to determine if Cliffords are drawn from the
            single qubit or two qubit clifford group
        max_clifford_idx
            Integer value used to set the index of the highest random
            clifford generated. Useful to generate e.g., simultaneous
            two qubit RB sequences.
        interleaving_clifford_id
            Integer value specifying the clifford ID that interleaves the
            sequence if desired
        apply_inverse_gate
            Flag for adding the inverse gate of the total clifford
            sequence before the :code:`meas_basis_index` gate.
        seed
            Integer value used as the seed to initialize the random
            number generator

        Returns
        -------
        :
            An integer list of clifford indices

        """

        if number_of_qubits == 1:
            Cl = SingleQubitCliffords
            group_size = np.min([24, max_clifford_idx])
        elif number_of_qubits == 2:
            Cl = TwoQubitCliffords
            group_size = np.min([11520, max_clifford_idx])
        else:
            raise NotImplementedError(
                "Randomized Benchmarking sequence generator is"
                "only implemented for one or two qubits",
            )

        # Generate a random sequence of Cliffords
        rng_seed = np.random.default_rng(seed)
        # creates the indices of the gate in each part of the sequence
        # (between 0 and group number) for the entireity of the sequence
        # length specified by n_cl.
        rb_clifford_indices = rng_seed.integers(0, group_size, n_cl).astype(np.uint32)

        # Add interleaving cliffords if applicable
        if interleaving_clifford_id is not None:
            rb_clif_ind_intl = np.empty(
                rb_clifford_indices.size * 2, dtype=np.uint32
            )  # 1D vector elongated to add in the interleaving
            # gates after every sequence
            rb_clif_ind_intl[0::2] = rb_clifford_indices
            rb_clif_ind_intl[1::2] = interleaving_clifford_id
            rb_clifford_indices = rb_clif_ind_intl

        # Add inverse gate if applicable
        # and measurement basis gate
        if apply_inverse_gate:
            # Calculate the net clifford
            net_clifford = self.calculate_net_clifford(rb_clifford_indices, Cl)
            rb_clifford_indices = np.append(
                rb_clifford_indices,
                self.calculate_recovery_clifford(
                    cl_in=net_clifford.idx,
                    desired_cl=np.uint32(meas_basis_index),
                    Clifford=Cl,
                ),
            )

        # ensure that the datatype is int
        rb_clifford_indices = rb_clifford_indices.astype(np.uint32)

        return rb_clifford_indices

    def schedule_function(
        self,
        seeds: int,
        number_of_cliffords: dict[str, np.ndarray],
        interleaving_clifford_id: int = None,
        apply_inverse_gate: bool = True,
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
            name = "tqg_randomized_benchmarking_ssro"
        else:
            name = "tqg_randomized_benchmarking_interleaved_ssro"
        schedule = Schedule(f"{name}")
        print("interleaved or not", name)
        shot = Schedule(f"shot")
        shot.add(IdlePulse(16e-9))

        # Initialize ClockResource with the first frequency value
        for this_qubit, this_transmon in self.transmons.items():
            ro_frequency = this_transmon.extended_clock_freqs.readout_3state_opt()
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.ro_3st_opt", freq=ro_frequency)
            )
            mw_frequency_01 = this_transmon.clock_freqs.f01()
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.01", freq=mw_frequency_01)
            )
            mw_frequency_12 = this_transmon.clock_freqs.f12()
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.12", freq=mw_frequency_12)
            )

        qubits = list(self.transmons.keys())
        coupler_names = self.couplers.keys()
        coupled_qubits = [coupler.split("_") for coupler in coupler_names]

        for index, this_coupler in enumerate(coupler_names):
            for index, this_coupler in enumerate(coupler_names):
                if this_coupler in ["q21_q22", "q22_q23", "q23_q24", "q24_q25"]:
                    downconvert = 0
                else:
                    downconvert = 4.4e9
                schedule.add_resource(
                    ClockResource(
                        name=f"{this_coupler}.cz",
                        freq=downconvert
                        - self.couplers[this_coupler].clock_freqs.cz_freq(),
                    )
                )
                shot.add_resource(
                    ClockResource(
                        name=f"{this_coupler}.cz",
                        freq=downconvert
                        - self.couplers[this_coupler].clock_freqs.cz_freq(),
                    )
                )

        print("coupler frequency is", self.couplers[this_coupler].clock_freqs.cz_freq())
        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = shot.add(Reset(*qubits), label="Start")

        # The first for loop iterates over all qubits:
        # for this_qubit, clifford_sequence_lengths in number_of_cliffords.items():
        clifford_sequence_lengths = list(number_of_cliffords.values())[0]

        # all_cliffords = len(cliffords.XY_decompositions)
        # rng = np.random.default_rng(seeds)

        # The inner for loop iterates over the random clifford sequence lengths
        for acq_index, this_number_of_cliffords in enumerate(
            clifford_sequence_lengths[:-3]
        ):
            # schedule.add(X(this_qubit))
            # random_sequence = rng.integers(all_cliffords, size=this_number_of_cliffords)

            start = shot.add(IdlePulse(16e-9))

            # for clifford_index, sequence_index in enumerate(random_sequence):
            # n_cl = 1
            index = 0
            
            # TODO: THIS FUNCTION NEEDS TO BE REPLACED
            clifford_seq = self.randomized_benchmarking_sequence(
                n_cl=this_number_of_cliffords,
                meas_basis_index=index,
                seed=seeds[next(iter(seeds))],
                interleaving_clifford_id=interleaving_clifford_id,
                apply_inverse_gate=apply_inverse_gate,
                number_of_qubits=2,
            )
            
            # TODO: THIS FUNCTION NEEDS TO BE REPLACED
            physical_gates = decompose_clifford_seq(
                clifford_seq, [qubits[0], qubits[1]]
            )
            
            separation_time = 300e-9
            
            reset = shot.add(Reset(*qubits))

            # TODO: THIS FUNCTION NEEDS TO BE REPLACED
            add_two_qubit_gates_to_schedule(
                shot, physical_gates, ref_op=reset, separation_time=separation_time
            )

            buffer = shot.add(IdlePulse(20e-9))
            for this_qubit in qubits:
                this_index = acq_index

                shot.add(
                    Measure_RO_3state_Opt(
                        this_qubit, acq_index=acq_index, bin_mode=BinMode.APPEND
                    ),
                    ref_op=buffer,
                    ref_pt="end",
                )
            root_relaxation = shot.add(Reset(*qubits), label=f"Reset_tqgRB_{acq_index}")

        for this_qubit in qubits:
            qubit_levels = range(self.qubit_state + 1)
            number_of_levels = len(qubit_levels)

            shot.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new="end"
            )  # To enforce parallelism we refer to the root relaxation
            # The intermediate for-loop iterates over all ro_amplitudes:
            # for ampl_indx, ro_amplitude in enumerate(ro_amplitude_values):
            # The inner for-loop iterates over all qubit levels:
            for level_index, state_level in enumerate(qubit_levels):
                calib_index = this_index + level_index + 1

                # print(f'{calib_index = }')
                if state_level == 0:
                    prep = shot.add(IdlePulse(40e-9))
                elif state_level == 1:
                    prep = shot.add(
                        X(this_qubit),
                    )
                elif state_level == 2:
                    shot.add(
                        X(this_qubit),
                    )
                    prep = shot.add(
                        Rxy_12(this_qubit),
                    )
                else:
                    raise ValueError("State Input Error")
                shot.add(
                    Measure_RO_3state_Opt(
                        this_qubit, acq_index=calib_index, bin_mode=BinMode.APPEND
                    ),
                    ref_op=prep,
                    ref_pt="end",
                )
                shot.add(Reset(this_qubit))

        schedule.add(IdlePulse(16e-9))
        print(schedule.add(shot, control_flow=Loop(repetitions), validate=False))
        schedule.add(IdlePulse(16e-9))

        return schedule
