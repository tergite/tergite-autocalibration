"""
The MIT License (MIT)

Copyright (c) 2016 DiCarlo lab-QuTech-Delft University of Technology

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import numpy as np
from typing import Optional

from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.two_qubit_clifford_group import (
    Clifford, SingleQubitClifford, TwoQubitClifford
)

def calculate_net_clifford(
        rb_clifford_indices: np.ndarray,
        Cliff:Clifford = SingleQubitClifford
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
    net_clifford = Cliff(0)  # assumes element 0 is the Identity
    for idx in rb_clifford_indices:
        # [2020-07-03 Victor] the `abs` below was to remove the sign that was
        # used to treat CZ as CZ and not the member of CNOT-like set of gates
        # Using negative sign convention (i.e. `-4368` for the interleaved CZ)
        # was a bad choice because there is no such thing as negative zero and
        # the clifford numer 0 is the identity that is necessary for
        # benchmarking an idling identity with the same duration as the time
        # allocated to the flux pulses, for example
        # cliff = Clifford(abs(idx))  # Deprecated!
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
        cliff = Cliff(idx % 100_000)

        # order of operators applied in is right to left, therefore
        # the new operator is applied on the left side.
        net_clifford = cliff * net_clifford

    return net_clifford

def randomized_benchmarking_sequence(
    n_cl: int,
    desired_net_cl: int = 0,
    number_of_qubits: int = 1,
    max_clifford_idx: int = 11520,
    interleaving_cl: Optional[int] = None,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Generates a randomized benchmarking sequence for the one or two qubit
    clifford group.

    Args:
        n_cl           (int) : number of Cliffords
        desired_net_cl (int) : idx of the desired net clifford, if None is
            specified no recovery Clifford is calculated
        number_of_qubits(int): used to determine if Cliffords are drawn
            from the single qubit or two qubit clifford group.
        max_clifford_idx (int): used to set the index of the highest random
            clifford generated. Useful to generate e.g., simultaneous two
            qubit RB sequences.
            FIXME: seems useless, because none of the callers set this for real, and we trim it to the group size
        interleaving_cl (int): interleaves the sequence with a specific
            clifford if desired
        seed           (int) : seed used to initialize the random number
            generator.
    Returns:
        list of clifford indices (ints)

    N.B. in the case of the 1 qubit clifford group this function does the
    same as "randomized_benchmarking_sequence_old" but
    does not use the 24 by 24 lookuptable method to calculate the
    net clifford. It instead uses the "Clifford" objects used in
    constructing the two qubit Clifford classes.
    The old method exists to establish the equivalence between the two methods.

    """

    if number_of_qubits == 1:
        Cl = SingleQubitClifford
        group_size = np.min([24, max_clifford_idx])
    elif number_of_qubits == 2:
        Cl = TwoQubitClifford
        group_size = np.min([11520, max_clifford_idx])
    else:
        raise NotImplementedError()

    # Generate a random sequence of Cliffords
    # Even if no seed is provided make sure we pick a new state such that
    # it is safe to run generate and compile the random sequences in
    # parallel using multiprocess
    rng_seed = np.random.RandomState(seed)
    rb_clifford_indices = rng_seed.randint(0, group_size, int(n_cl))

    # Add interleaving cliffords if applicable
    if interleaving_cl is not None:
        rb_clif_ind_intl = np.empty(rb_clifford_indices.size * 2, dtype=int)
        rb_clif_ind_intl[0::2] = rb_clifford_indices
        rb_clif_ind_intl[1::2] = interleaving_cl
        rb_clifford_indices = rb_clif_ind_intl

    if desired_net_cl is not None:
        # Calculate the net clifford
        net_clifford = calculate_net_clifford(rb_clifford_indices, Cl)

        # determine the inverse of the sequence
        recovery_to_idx_clifford = net_clifford.get_inverse()
        recovery_clifford = Cl(desired_net_cl) * recovery_to_idx_clifford
        rb_clifford_indices = np.append(rb_clifford_indices, recovery_clifford.idx)
    return rb_clifford_indices