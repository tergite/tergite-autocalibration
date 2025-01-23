# This project includes code licensed under the MIT License (MIT):
# Copyright (c) 2016 DiCarlo lab-QuTech-Delft University of Technology
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
# Modifications made by (C) Copyright Chalmers Next Labs 2025 are licensed under 
# the Apache License, Version 2.0.
#
# You may obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np
from numpy.typing import NDArray
from typing import Optional, Iterable
from quantify_scheduler import Schedule
from quantify_scheduler.backends.qblox.constants import MIN_TIME_BETWEEN_OPERATIONS
from quantify_scheduler.operations.gate_library import CZ, X90, Y90, Measure, Reset, Rxy, X, Y

from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.two_qubit_clifford_group import (
    Clifford, SingleQubitClifford, TwoQubitClifford, common_cliffords
)

def calculate_net_clifford(
        rb_clifford_indices: np.ndarray,
        Clifford: type[Clifford] = SingleQubitClifford
) -> Clifford:
    """
    Calculate the net-clifford from a list of cliffords indices.

    Args:
        rb_clifford_indices: list or array of integers specifying the cliffords.
        Cliff : Clifford object used to determine what
            inversion technique to use and what indices are valid.
            Valid choices are `SingleQubitClifford` and `TwoQubitClifford`

    Returns:
        net_clifford: a `Clifford` object containing the net-clifford.
            the Clifford index is contained in the Clifford.idx attribute.

    Note: the order corresponds to the order in a pulse sequence but is
        the reverse of what it would be in a chained dot product.
    """

    # Calculate the net clifford
    net_clifford = Clifford(0)  # assumes element 0 is the Identity
    for idx in rb_clifford_indices:
        assert idx > -1, (
            "The convention for interleaved gates has changed! "
            + "See notes in this function. "
            + "You probably need to specify {}".format(100_000 + abs(idx))
        )
        # In order to benchmark specific gates (and not cliffords), e.g. CZ but
        # not as a member of the CNOT-like set of gates, or an identity with
        # the same duration as the CZ we use, by convention, when specifying
        # the interleaved gate, the index of the corresponding
        # clifford + 100000, this is to keep it readable and bigger than the
        # 11520 elements of the Two-qubit Clifford group C2
        # corresponding clifford
        cliff = Clifford(idx % 100_000)

        # order of operators applied in is right to left, therefore
        # the new operator is applied on the left side.
        net_clifford = cliff * net_clifford

    return net_clifford

def randomized_benchmarking_sequence(
    n_cl: int,
    apply_inverse_gate: bool = True,
    number_of_qubits: int = 1,
    max_clifford_idx: int = 11520,
    interleaving_clifford_id: Optional[int] = None,
    seed: Optional[int] = None,
) -> NDArray[np.int_]:
    """
    Generates a randomized benchmarking sequence for the one or two qubit Clifford group.

    Args:
        n_cl           (int) : number of Cliffords
        apply_inverse_gate (bool) : Apply the recovery Clifford gate.
        number_of_qubits(int): used to determine if Cliffords are drawn
            from the single qubit or two qubit clifford group.
        max_clifford_idx (int): used to set the index of the highest random
            clifford generated. Useful to generate e.g., simultaneous two
            qubit RB sequences.
        interleaving_clifford_id (Optional[int]): Specific Clifford index to interleave 
            throughout the sequence, if provided.
        seed (Optional[int]): Seed for the random number generator.
    Returns:
        np.ndarray: Array of Clifford indices representing the randomized benchmarking sequence.
    """
    
    if n_cl < 0:
        raise ValueError("Number of Cliffords must be non-negative")

    if number_of_qubits == 1:
        Cl = SingleQubitClifford
        group_size = np.min([24, max_clifford_idx])
    elif number_of_qubits == 2:
        Cl = TwoQubitClifford
        group_size = np.min([11520, max_clifford_idx])
    else:
        raise NotImplementedError("Only one- and two-qubit Clifford groups are supported.")

    # Generate a random sequence of Cliffords
    # Even if no seed is provided make sure we pick a new state such that
    # it is safe to run generate and compile the random sequences in
    # parallel using multiprocess
    rng_seed = np.random.default_rng(seed)
    rb_clifford_indices = rng_seed.integers(0, group_size, n_cl)

    # Add interleaving cliffords if applicable
    if interleaving_clifford_id is not None:
        rb_clif_ind_intl = np.empty(rb_clifford_indices.size * 2, dtype=int)
        rb_clif_ind_intl[0::2] = rb_clifford_indices
        rb_clif_ind_intl[1::2] = interleaving_clifford_id
        rb_clifford_indices = rb_clif_ind_intl

    # Add inverse clifford gate if applicable
    if apply_inverse_gate:
        # Calculate the net clifford
        net_clifford = calculate_net_clifford(rb_clifford_indices, Cl)

        # determine the inverse of the sequence
        recovery_clifford = Cl(net_clifford.idx).get_inverse() * net_clifford.get_inverse()
        rb_clifford_indices = np.append(rb_clifford_indices, recovery_clifford.idx)
        
    return rb_clifford_indices