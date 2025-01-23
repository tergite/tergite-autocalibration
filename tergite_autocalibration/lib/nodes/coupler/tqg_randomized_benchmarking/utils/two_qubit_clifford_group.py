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
from typing import List, Optional
from zlib import crc32
from os.path import join, dirname, abspath
from numpy.typing import NDArray
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.clifford_group import clifford_group_single_qubit as C1, CZ, S1
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.clifford_decomposition import epstein_efficient_decomposition

hash_dir = join(abspath(dirname(__file__)), 'clifford_hash_tables')

"""
This file contains Clifford decompositions for the two qubit Clifford group.

The Clifford decomposition closely follows two papers:
Corcoles et al. Process verification ... Phys. Rev. A. 2013
    http://journals.aps.org/pra/pdf/10.1103/PhysRevA.87.030301
for the different classes of two-qubit Cliffords.

and
Barends et al. Superconducting quantum circuits at the ... Nature 2014
    https://www.nature.com/articles/nature13171?lang=en
for writing the cliffords in terms of CZ gates.


###########################################################################
2-qubit clifford decompositions

The two qubit clifford group (C2) consists of 11520 two-qubit cliffords
These gates can be subdivided into four classes.
    1. The Single-qubit like class  | 576 elements  (24^2)
    2. The CNOT-like class          | 5184 elements (24^2 * 3^2)
    3. The iSWAP-like class         | 5184 elements (24^2 * 3^2)
    4. The SWAP-like class          | 576  elements (24^2)
    --------------------------------|------------- +
    Two-qubit Clifford group C2     | 11520 elements


1. The Single-qubit like class
    -- C1 --
    -- C1 --

2. The CNOT-like class
    --C1--•--S1--      --C1--•--S1------
          |        ->        |
    --C1--⊕--S1--      --C1--•--S1^Y90--

3. The iSWAP-like class
    --C1--*--S1--     --C1--•---Y90--•--S1^Y90--
          |       ->        |        |
    --C1--*--S1--     --C1--•--mY90--•--S1^X90--

4. The SWAP-like class
    --C1--x--     --C1--•-mY90--•--Y90--•-------
          |   ->        |       |       |
    --C1--x--     --C1--•--Y90--•-mY90--•--Y90--

C1: element of the single qubit Clifford group
    N.B. we use the decomposition defined in Epstein et al. here

S1: element of the S1 group, a subgroup of the single qubit Clifford group

S1[0] = I
S1[1] = rY90, rX90
S1[2] = rXm90, rYm90

Important clifford indices:

        I    : Cl 0
        X90  : Cl 16
        Y90  : Cl 21
        X180 : Cl 3
        Y180 : Cl 6
        Z180 : Cl 9
        CZ   : 4368

"""
# set as a module wide variable instead of argument to function for speed
# reasons
gate_decomposition = epstein_efficient_decomposition

# used to transform the S1 subgroup
X90 = C1[16]
Y90 = C1[21]
mY90 = C1[15]

# A dict containing clifford IDs with common names.
common_cliffords = {
    'I': 0, 
    'X': 3, 
    'Y': 6, 
    'Z': 9,
    'II': 0, 
    'IX': 3, 
    'IY': 6, 
    'IZ': 9,
    'XI': 24*3 + 0, 
    'XX': 24*3 + 3,
    'XY': 24*3 + 6, 
    'XZ': 24*3 + 9,
    'YI': 24*6 + 0, 
    'YX': 24*6 + 3,
    'YY': 24*6 + 6, 
    'YZ': 24*6 + 9,
    'ZI': 24*9 + 0, 
    'ZX': 24*9 + 3,
    'ZY': 24*9 + 6,
    'ZZ': 24*9 + 9,
    'X90':  16,
    'Y90':  21,
    'X180':  3,
    'Y180':  6,
    'Z180':  9,
    'CZ': 104368,
}

class Clifford:
    """
    Base class for Clifford gates.
    """
    
    # Class variable for hash table
    _hash_table: Optional[List[int]] = None
    pauli_transfer_matrix: Optional[NDArray]
    idx: int
    
        
    def __init__(self, idx: int):
        raise NotImplementedError

    def __mul__(self, other: 'Clifford') -> 'Clifford':
        """
        Compute the product of two Clifford gates.

        Args:
            other (Clifford): Another Clifford gate.

        Returns:
            Clifford: A new Clifford object representing the product operation.
        """
        net_op = np.dot(self.pauli_transfer_matrix,
                        other.pauli_transfer_matrix)
        idx = self._get_clifford_id(net_op)
        return self.__class__(idx)

    def __repr__(self):
        return f'{self.__class__.__name__}(idx={self.idx})'

    def __str__(self):
        return self.__repr__

    def get_inverse(self):
        inverse_ptm = np.linalg.inv(self.pauli_transfer_matrix).astype(int)
        idx = self._get_clifford_id(inverse_ptm)
        return self.__class__(idx)

    @classmethod
    def _get_clifford_id(cls, pauli_transfer_matrix):
        raise NotImplementedError


class SingleQubitClifford(Clifford):
    # class constants
    GRP_SIZE: int = 24

    # class variablesps
    _gate_decompositions = [[] for _ in range(GRP_SIZE)]

    def __init__(self, idx: int, qubit_idx: int=0) -> None:
        if not 0 <= idx < self.GRP_SIZE:
            raise ValueError(f"Invalid Clifford index: {idx}. Must be 0 <= idx < {self.GRP_SIZE}")
        self.idx = idx
        self.qubit_idx = qubit_idx
        self.pauli_transfer_matrix = C1[idx]

    @property  # FIXME: remove
    def gate_decomposition(self):
        """
        Returns the gate decomposition of the single qubit Clifford group
        according to the decomposition by Epstein et al.
        """
        if self._gate_decompositions[self.idx] is None:
            _gate_decomposition = [(g, f'q{self.qubit_idx}') for g in gate_decomposition[self.idx]]
            self._gate_decompositions[self.idx] = _gate_decomposition
        return self._gate_decompositions[self.idx]
    
    @classmethod
    def _get_clifford_id(cls, pauli_transfer_matrix):
        """
        returns the unique Id of a Clifford.
        """
        unique_hash = crc32(pauli_transfer_matrix.astype(int))

        if cls._hash_table is None:
            cls._hash_table = get_single_qubit_clifford_hash_table()

        idx = cls._hash_table.index(unique_hash)
        return idx


class TwoQubitClifford(Clifford):
    # class constants
    GRP_SIZE_CLIFFORD = SingleQubitClifford.GRP_SIZE
    GRP_SIZE_SINGLE_QUBIT = GRP_SIZE_CLIFFORD**2
    GRP_SIZE_S1 = 3  # the S1 subgroup of SingleQubitClifford
    GRP_SIZE_CNOT = GRP_SIZE_SINGLE_QUBIT * GRP_SIZE_S1**2
    GRP_SIZE_ISWAP = GRP_SIZE_CNOT
    GRP_SIZE_SWAP = GRP_SIZE_SINGLE_QUBIT
    GRP_SIZE = GRP_SIZE_SINGLE_QUBIT + GRP_SIZE_CNOT + GRP_SIZE_ISWAP + GRP_SIZE_SWAP

    assert(GRP_SIZE_SINGLE_QUBIT == 576)
    assert(GRP_SIZE_CNOT == 5184)
    assert(GRP_SIZE == 11520)

    # class variables
    _gate_decompositions = [[] for _ in range(GRP_SIZE)]
    _pauli_transfer_matrices: List[Optional[NDArray]] = [None] * GRP_SIZE

    def __init__(self, idx: int):
        if not 0 <= idx < self.GRP_SIZE:
            raise ValueError(f"Invalid Clifford index: {idx}. Must be 0 <= idx < {self.GRP_SIZE}")
        self.idx = idx

    @property  # FIXME: remove
    def pauli_transfer_matrix(self):
        # check cache
        if self._pauli_transfer_matrices[self.idx] is None:
            # compute
            if self.idx < 576:
                _pauli_transfer_matrix = self.single_qubit_like_PTM(self.idx)
            elif self.idx < 576 + 5184:
                _pauli_transfer_matrix = self.CNOT_like_PTM(self.idx-576)
            elif self.idx < 576 + 2*5184:
                _pauli_transfer_matrix = self.iSWAP_like_PTM(self.idx-(576+5184))
            else:  # NB: GRP_SIZE checked upon construction
                _pauli_transfer_matrix = self.SWAP_like_PTM(self.idx-(576+2*5184))

            # store in cache
            self._pauli_transfer_matrices[self.idx] = _pauli_transfer_matrix

        return self._pauli_transfer_matrices[self.idx]

    @property  # FIXME: remove
    def gate_decomposition(self):
        """
        Returns the gate decomposition of the two qubit Clifford group.

        Single qubit Cliffords are decomposed according to Epstein et al.
        """

        # check cache
        if self._gate_decompositions[self.idx] is None:
            # compute
            if self.idx < 576:
                _gate_decomposition = self.single_qubit_like_gates(self.idx)
            elif self.idx < 576 + 5184:
                _gate_decomposition = self.CNOT_like_gates(self.idx-576)
            elif self.idx < 576 + 2*5184:
                _gate_decomposition = self.iSWAP_like_gates(self.idx-(576+5184))
            else:  # NB: GRP_SIZE checked upon construction
                _gate_decomposition = self.SWAP_like_gates(self.idx-(576+2*5184))

            # store in cache
            self._gate_decompositions[self.idx] = _gate_decomposition

        return self._gate_decompositions[self.idx]

    @classmethod
    def _get_clifford_id(cls, pauli_transfer_matrix) -> int:
        """
        returns the unique Id of a Clifford.
        """
        unique_hash = crc32(pauli_transfer_matrix.astype(int))

        if cls._hash_table is None:
            cls._hash_table = get_two_qubit_clifford_hash_table()

        idx = cls._hash_table.index(unique_hash)
        return idx

    @classmethod
    def single_qubit_like_PTM(cls, idx: int):
        """
        Returns the pauli transfer matrix for gates of the single qubit like class
            (q0)  -- C1 --
            (q1)  -- C1 --
        """
        assert(idx < cls.GRP_SIZE_SINGLE_QUBIT)
        idx_q0 = idx % 24
        idx_q1 = idx // 24
        pauli_transfer_matrix = np.kron(C1[idx_q1], C1[idx_q0])
        return pauli_transfer_matrix

    @classmethod
    def single_qubit_like_gates(cls, idx: int):
        """
        Returns the gates for Cliffords of the single qubit like class
            (q0)  -- C1 --
            (q1)  -- C1 --
        """
        assert(idx < cls.GRP_SIZE_SINGLE_QUBIT)
        idx_q0 = idx % 24
        idx_q1 = idx // 24

        g_q0 = [(g, 'q0') for g in gate_decomposition[idx_q0]]
        g_q1 = [(g, 'q1') for g in gate_decomposition[idx_q1]]
        gates = g_q0 + g_q1
        return gates

    @classmethod
    def CNOT_like_PTM(cls, idx: int):
        """
        Returns the pauli transfer matrix for gates of the cnot like class
            (q0)  --C1--•--S1--      --C1--•--S1------
                        |        ->        |
            (q1)  --C1--⊕--S1--      --C1--•--S1^Y90--
        """
        assert(idx < cls.GRP_SIZE_CNOT)
        idx_0 = idx % 24
        idx_1 = (idx // 24) % 24
        idx_2 = (idx // 576) % 3
        idx_3 = (idx // 1728)

        C1_q0 = np.kron(np.eye(4), C1[idx_0])
        C1_q1 = np.kron(C1[idx_1], np.eye(4))
        # CZ
        S1_q0 = np.kron(np.eye(4), S1[idx_2])
        S1y_q1 = np.kron(np.dot(C1[idx_3], Y90), np.eye(4))
        return np.linalg.multi_dot(list(reversed([C1_q0, C1_q1, CZ, S1_q0, S1y_q1])))

    @classmethod
    def CNOT_like_gates(cls, idx: int):
        """
        Returns the gates for Cliffords of the cnot like class
            (q0)  --C1--•--S1--      --C1--•--S1------
                        |        ->        |
            (q1)  --C1--⊕--S1--      --C1--•--S1^Y90--
        """
        assert(idx < cls.GRP_SIZE_CNOT)
        idx_0 = idx % 24
        idx_1 = (idx // 24) % 24
        idx_2 = (idx // 576) % 3
        idx_3 = (idx // 1728)

        C1_q0 = [(g, 'q0') for g in gate_decomposition[idx_0]]
        C1_q1 = [(g, 'q1') for g in gate_decomposition[idx_1]]
        CZ = [('CZ', ['q0', 'q1'])]

        idx_2s = SingleQubitClifford._get_clifford_id(S1[idx_2])
        S1_q0 = [(g, 'q0') for g in gate_decomposition[idx_2s]]
        # FIXME: precomputation of these 3 entries would be more efficient (more similar occurrences in this file):
        idx_3s = SingleQubitClifford._get_clifford_id(np.dot(C1[idx_3], Y90))
        S1_yq1 = [(g, 'q1') for g in gate_decomposition[idx_3s]]

        gates = C1_q0 + C1_q1 + CZ + S1_q0 + S1_yq1
        return gates

    @classmethod
    def iSWAP_like_PTM(cls, idx: int):
        """
        Returns the pauli transfer matrix for gates of the iSWAP like class
            (q0)  --C1--*--S1--     --C1--•---Y90--•--S1^Y90--
                        |       ->        |        |
            (q1)  --C1--*--S1--     --C1--•--mY90--•--S1^X90--
        """
        assert(idx < cls.GRP_SIZE_ISWAP)
        idx_0 = idx % 24
        idx_1 = (idx // 24) % 24
        idx_2 = (idx // 576) % 3
        idx_3 = (idx // 1728)

        C1_q0 = np.kron(np.eye(4), C1[idx_0])
        C1_q1 = np.kron(C1[idx_1], np.eye(4))
        # CZ
        sq_swap_gates = np.kron(mY90, Y90)
        # CZ
        S1_q0 = np.kron(np.eye(4), np.dot(S1[idx_2], Y90))
        S1y_q1 = np.kron(np.dot(C1[idx_3], X90), np.eye(4))

        return np.linalg.multi_dot(list(reversed([C1_q0, C1_q1,
                                                  CZ, sq_swap_gates, CZ,
                                                  S1_q0, S1y_q1])))

    @classmethod
    def iSWAP_like_gates(cls, idx: int):
        """
        Returns the gates for Cliffords of the iSWAP like class
            (q0)  --C1--*--S1--     --C1--•---Y90--•--S1^Y90--
                        |       ->        |        |
            (q1)  --C1--*--S1--     --C1--•--mY90--•--S1^X90--
        """
        assert(idx < cls.GRP_SIZE_ISWAP)
        idx_0 = idx % 24
        idx_1 = (idx // 24) % 24
        idx_2 = (idx // 576) % 3
        idx_3 = (idx // 1728)

        C1_q0 = [(g, 'q0') for g in gate_decomposition[idx_0]]
        C1_q1 = [(g, 'q1') for g in gate_decomposition[idx_1]]
        CZ = [('CZ', ['q0', 'q1'])]

        sqs_idx_q0 = SingleQubitClifford._get_clifford_id(Y90)
        sqs_idx_q1 = SingleQubitClifford._get_clifford_id(mY90)
        sq_swap_gates_q0 = [(g, 'q0') for g in gate_decomposition[sqs_idx_q0]]
        sq_swap_gates_q1 = [(g, 'q1') for g in gate_decomposition[sqs_idx_q1]]

        idx_2s = SingleQubitClifford._get_clifford_id(np.dot(S1[idx_2], Y90))
        S1_q0 = [(g, 'q0') for g in gate_decomposition[idx_2s]]
        idx_3s = SingleQubitClifford._get_clifford_id(np.dot(C1[idx_3], X90))
        S1y_q1 = [(g, 'q1') for g in gate_decomposition[idx_3s]]

        gates = (C1_q0 + C1_q1 + CZ +
                 sq_swap_gates_q0 + sq_swap_gates_q1 + CZ +
                 S1_q0 + S1y_q1)
        return gates

    @classmethod
    def SWAP_like_PTM(cls, idx: int) -> np.ndarray:
        """
        Returns the pauli transfer matrix for gates of the SWAP like class

        (q0)  --C1--x--     --C1--•-mY90--•--Y90--•-------
                    |   ->        |       |       |
        (q1)  --C1--x--     --C1--•--Y90--•-mY90--•--Y90--
        """
        assert(idx < cls.GRP_SIZE_SWAP)
        idx_q0 = idx % 24
        idx_q1 = idx // 24
        sq_like_cliff = np.kron(C1[idx_q1], C1[idx_q0])
        sq_swap_gates_0 = np.kron(Y90, mY90)
        sq_swap_gates_1 = np.kron(mY90, Y90)
        sq_swap_gates_2 = np.kron(Y90, np.eye(4))

        return np.linalg.multi_dot(list(reversed([sq_like_cliff, CZ,
                                                  sq_swap_gates_0, CZ,
                                                  sq_swap_gates_1, CZ,
                                                  sq_swap_gates_2])))

    @classmethod
    def SWAP_like_gates(cls, idx: int):
        """
        Returns the gates for Cliffords of the SWAP like class

        (q0)  --C1--x--     --C1--•-mY90--•--Y90--•-------
                    |   ->        |       |       |
        (q1)  --C1--x--     --C1--•--Y90--•-mY90--•--Y90--
        """
        assert(idx < cls.GRP_SIZE_SWAP)
        idx_q0 = idx % 24
        idx_q1 = idx // 24
        C1_q0 = [(g, 'q0') for g in gate_decomposition[idx_q0]]
        C1_q1 = [(g, 'q1') for g in gate_decomposition[idx_q1]]
        CZ = [('CZ', ['q0', 'q1'])]

        # sq_swap_gates_0 = np.kron(Y90, mY90)

        sqs_idx_q0 = SingleQubitClifford._get_clifford_id(mY90)
        sqs_idx_q1 = SingleQubitClifford._get_clifford_id(Y90)
        sq_swap_gates_0_q0 = [(g, 'q0') for g in gate_decomposition[sqs_idx_q0]]
        sq_swap_gates_0_q1 = [(g, 'q1') for g in gate_decomposition[sqs_idx_q1]]

        sqs_idx_q0 = SingleQubitClifford._get_clifford_id(Y90)
        sqs_idx_q1 = SingleQubitClifford._get_clifford_id(mY90)
        sq_swap_gates_1_q0 = [(g, 'q0') for g in gate_decomposition[sqs_idx_q0]]
        sq_swap_gates_1_q1 = [(g, 'q1') for g in gate_decomposition[sqs_idx_q1]]

        sqs_idx_q1 = SingleQubitClifford._get_clifford_id(Y90)
        sq_swap_gates_2_q0 = [(g, 'q0') for g in gate_decomposition[0]]
        sq_swap_gates_2_q1 = [(g, 'q1') for g in gate_decomposition[sqs_idx_q1]]

        gates = (C1_q0 + C1_q1 + CZ +
                 sq_swap_gates_0_q0 + sq_swap_gates_0_q1 + CZ +
                 sq_swap_gates_1_q0 + sq_swap_gates_1_q1 + CZ +
                 sq_swap_gates_2_q0 + sq_swap_gates_2_q1)
        return gates


##############################################################################
# It is important that this check is after the Clifford objects as otherwise
# it is impossible to generate the hash tables
##############################################################################
try:
    open(join(hash_dir, 'single_qubit_hash_lut.txt'), 'r')
    # FIXME: also check 'two_qubit_hash_lut.txt'
except FileNotFoundError:
    print("Clifford group hash tables not detected.")
    from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.generate_clifford_hash_tables import generate_hash_tables
    generate_hash_tables()


def get_single_qubit_clifford_hash_table():
    """
    Get's the single qubit clifford hash table. Requires this to be generated
    first. To generate, execute "generate_clifford_hash_tables.py".
    """
    with open(join(hash_dir, 'single_qubit_hash_lut.txt'), 'r') as f:
        hash_table = [int(line.rstrip('\n')) for line in f]
    return hash_table


def get_two_qubit_clifford_hash_table():
    """
    Get's the two qubit clifford hash table. Requires this to be generated
    first. To generate, execute "generate_clifford_hash_tables.py".
    """
    with open(join(hash_dir, 'two_qubit_hash_lut.txt'), 'r') as f:
        hash_table = [int(line.rstrip('\n')) for line in f]
    return hash_table