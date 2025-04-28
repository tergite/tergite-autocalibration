# This code is part of Tergite
#
# Modifications copyright (C) Pontus Vikstål 2025
# Modifications copyright (C) Chalmers Next Labs 2025
#
# This program is derived from the PycQED with the following license:
#
# MIT License
#
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

import numpy as np
from .pauli_transfer_matrices import I, X, Y, Z, S, S2, H, CZ
from typing import List, Tuple, Dict, ClassVar

# The decomposition of the single qubit clifford group as per
# Epstein et al. Phys. Rev. A 89, 062321 (2014)
# Note: Explicitly reversing order because order of operators is order in time
epstein_efficient_decomposition = [[] for _ in range(24)]
epstein_efficient_decomposition[0] = ["I"]
epstein_efficient_decomposition[1] = ["Y90", "X90"]
epstein_efficient_decomposition[2] = ["mX90", "mY90"]
epstein_efficient_decomposition[3] = ["X180"]
epstein_efficient_decomposition[4] = ["mY90", "mX90"]
epstein_efficient_decomposition[5] = ["X90", "mY90"]
epstein_efficient_decomposition[6] = ["Y180"]
epstein_efficient_decomposition[7] = ["mY90", "X90"]
epstein_efficient_decomposition[8] = ["X90", "Y90"]
epstein_efficient_decomposition[9] = ["X180", "Y180"]
epstein_efficient_decomposition[10] = ["Y90", "mX90"]
epstein_efficient_decomposition[11] = ["mX90", "Y90"]
epstein_efficient_decomposition[12] = ["Y90", "X180"]
epstein_efficient_decomposition[13] = ["mX90"]
epstein_efficient_decomposition[14] = ["X90", "mY90", "mX90"]
epstein_efficient_decomposition[15] = ["mY90"]
epstein_efficient_decomposition[16] = ["X90"]
epstein_efficient_decomposition[17] = ["X90", "Y90", "X90"]
epstein_efficient_decomposition[18] = ["mY90", "X180"]
epstein_efficient_decomposition[19] = ["X90", "Y180"]
epstein_efficient_decomposition[20] = ["X90", "mY90", "X90"]
epstein_efficient_decomposition[21] = ["Y90"]
epstein_efficient_decomposition[22] = ["mX90", "Y180"]
epstein_efficient_decomposition[23] = ["X90", "Y90", "mX90"]

# The single qubit clifford group where each element is a 4x4 pauli transfer matrix
# Note: Explictly reversing order because order of operators is order in time
C1 = [np.empty([4, 4])] * (24)
C1[0] = np.linalg.multi_dot([I, I, I][::-1])
C1[1] = np.linalg.multi_dot([I, I, S][::-1])
C1[2] = np.linalg.multi_dot([I, I, S2][::-1])
C1[3] = np.linalg.multi_dot([X, I, I][::-1])
C1[4] = np.linalg.multi_dot([X, I, S][::-1])
C1[5] = np.linalg.multi_dot([X, I, S2][::-1])
C1[6] = np.linalg.multi_dot([Y, I, I][::-1])
C1[7] = np.linalg.multi_dot([Y, I, S][::-1])
C1[8] = np.linalg.multi_dot([Y, I, S2][::-1])
C1[9] = np.linalg.multi_dot([Z, I, I][::-1])
C1[10] = np.linalg.multi_dot([Z, I, S][::-1])
C1[11] = np.linalg.multi_dot([Z, I, S2][::-1])
C1[12] = np.linalg.multi_dot([I, H, I][::-1])
C1[13] = np.linalg.multi_dot([I, H, S][::-1])
C1[14] = np.linalg.multi_dot([I, H, S2][::-1])
C1[15] = np.linalg.multi_dot([X, H, I][::-1])
C1[16] = np.linalg.multi_dot([X, H, S][::-1])
C1[17] = np.linalg.multi_dot([X, H, S2][::-1])
C1[18] = np.linalg.multi_dot([Y, H, I][::-1])
C1[19] = np.linalg.multi_dot([Y, H, S][::-1])
C1[20] = np.linalg.multi_dot([Y, H, S2][::-1])
C1[21] = np.linalg.multi_dot([Z, H, I][::-1])
C1[22] = np.linalg.multi_dot([Z, H, S][::-1])
C1[23] = np.linalg.multi_dot([Z, H, S2][::-1])

# used in the CNOT-, iSWAP-, and SWAP-like gates
X90 = C1[16]
Y90 = C1[21]
mY90 = C1[15]

# The S1 exchange group is a subgroup of C1 (single qubit Clifford group)
# and is used when generating C2 (two qubit Clifford group)
S1 = [
    C1[0],
    C1[1],
    C1[2],
]


class Clifford:
    """Base class for Clifford

    Abstract base class for all Clifford operations.

    Attributes:
        idx (int): Index of the Clifford operation
        GROUP_SIZE (ClassVar[int]): Size of the Clifford group
        CLIFFORD_HASH_TABLE (CLassVar[Dict[int, int]]): Hash table for fast lookup of Clifford indices
    """

    CLIFFORD_HASH_TABLE: ClassVar[Dict[int, int]]
    GROUP_SIZE: ClassVar[int]

    def __init__(self, idx: int) -> None:
        """Initialize the Clifford object with a given index

        Args:
            idx (int): Index of the Clifford operation

        Attributes:
            idx (int): Index of the Clifford operation

        Raises:
            ValueError: If the index is not valid (0 <= idx < GROUP_SIZE)
        """
        if not 0 <= idx < self.GROUP_SIZE:
            raise ValueError(
                f"Invalid Clifford index: {idx}. Must be 0 <= idx < {self.GROUP_SIZE}"
            )
        self.idx = idx

    def __mul__(self, other: "Clifford") -> "Clifford":
        """Multiply two Clifford operations

        Args:
            other (Clifford): Another Clifford operation

        Returns:
            Clifford: The product of the two Clifford Pauli Transfer Matrices

        Raises:
            TypeError: If other is not the same type of Clifford
        """
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Cannot multiply {self.__class__.__name__} with {other.__class__.__name__}"
            )

        net_op = np.dot(self.pauli_transfer_matrix, other.pauli_transfer_matrix)
        idx = self.find_clifford_index(net_op)
        return self.__class__(idx)

    def __eq__(self, other: "Clifford") -> bool:
        """Check if two Clifford operations are equal.

        Args:
            other (Clifford): Another Clifford operation

        Returns:
            bool: True if the operations are equal, False otherwise
        """
        if not isinstance(other, self.__class__):
            return False
        return self.idx == other.idx

    def get_inverse(self) -> "Clifford":
        """Get the inverse of this Clifford operation

        Returns:
            Clifford: The inverse operation
        """
        inverse_ptm = np.linalg.inv(self.pauli_transfer_matrix).astype(int)
        idx = self.find_clifford_index(inverse_ptm)
        return self.__class__(idx)

    @property
    def pauli_transfer_matrix(self) -> np.ndarray:
        """Returns the Pauli transfer matrix of the Clifford operation.

        Returns:
            np.ndarray: The Pauli transfer matrix
        """
        raise NotImplementedError("Subclasses must implement pauli_transfer_matrix")

    @property
    def gate_decomposition(self) -> List[Tuple[List[str], str]]:
        """Returns the gate decomposition of the Clifford gate

        Returns:
            List: Gate decomposition as a list of tuples (gate_name, qubit_identifier)
        """
        raise NotImplementedError("Subclasses must implement gate_decomposition")

    @classmethod
    def find_clifford_index(cls, matrix: np.ndarray) -> int:
        """Find the index of a Clifford matrix using hash lookup

        Args:
            matrix (np.ndarray): The Pauli transfer matrix

        Returns:
            int: The index of the Clifford operation

        Raises:
            ValueError: If the Clifford index is not found
        """

        # Create Hash Table if it is empty
        if not cls.CLIFFORD_HASH_TABLE:
            for idx in range(cls.GROUP_SIZE):
                ptm = cls(idx=idx).pauli_transfer_matrix
                hash_value = cls._hash_matrix(ptm)
                cls.CLIFFORD_HASH_TABLE[hash_value] = idx

        hash_value = cls._hash_matrix(matrix)
        # Look up if the hash values is in our hash table
        if hash_value in cls.CLIFFORD_HASH_TABLE:
            return cls.CLIFFORD_HASH_TABLE[hash_value]

        raise ValueError("Clifford index not found.")

    @staticmethod
    def _hash_matrix(matrix: np.ndarray) -> int:
        """Create a hash value for a matrix using NumPy's internal representation.

        Use the byte representation of the rounded integer matrix.

        Args:
            matrix (np.ndarray): The Pauli transfer matrix to hash

        Returns:
            int: Hash value of the Pauli transfer matrix
        """
        return hash(matrix.round().astype(int).tobytes())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(idx={self.idx})"


class SingleQubitClifford(Clifford):
    """Single Qubit Clifford gate class

    The decomposition of the single qubit clifford group follows paper
    Epstein et al. Phys. Rev. A 89, 062321 (2014)
    """

    # Class Variables
    CLIFFORD_HASH_TABLE = {}  # Initialize the hash table

    # Class Constants
    GROUP_SIZE = 24  # Size of the single qubit Clifford group

    @property
    def pauli_transfer_matrix(self) -> np.ndarray:
        """Returns the Pauli transfer matrix of the single qubit Clifford operation"""
        return C1[self.idx]

    @property
    def gate_decomposition(self) -> List[Tuple[List[str], str]]:
        """
        Returns the gate decomposition of the single qubit Clifford group
        according to the decomposition by Epstein et al.

        Returns:
            List of tuples where each tuple contains (gate_name, qubit_identifier)
        """
        gate_decomp = [(g, "q0") for g in epstein_efficient_decomposition[self.idx]]
        return gate_decomp


class TwoQubitClifford(Clifford):
    """Two Qubit Clifford gate class

    The Clifford decomposition closely follows two papers:

    1. Corcoles et al. Process verification ... Phys. Rev. A. 2013
    http://journals.aps.org/pra/pdf/10.1103/PhysRevA.87.030301
    for the different classes of two-qubit Cliffords.

    2. Barends et al. Superconducting quantum circuits at the ... Nature 2014
    https://www.nature.com/articles/nature13171?lang=en
    for writing the cliffords in terms of CZ gates.

    2-qubit clifford decompositions
    -------------------------------
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
        Note: We use the decomposition defined in Epstein et al. here

    S1: element of the S1 group, a subgroup of the single qubit Clifford group
    """

    # Class Variables
    CLIFFORD_HASH_TABLE = {}
    _PTM_CACHE = {}  # Initialize the cache for PTMs
    _GATE_DECOMP_CACHE = {}  # Initialize the cache for gate decompositions

    # Class Constants
    GROUP_SIZE_CLIFFORD = 24
    GROUP_SIZE_SINGLE_QUBIT = GROUP_SIZE_CLIFFORD**2
    GROUP_SIZE_S1 = 3  # the S1 subgroup of SingleQubitClifford
    GROUP_SIZE_CNOT = GROUP_SIZE_SINGLE_QUBIT * GROUP_SIZE_S1**2
    GROUP_SIZE_ISWAP = GROUP_SIZE_CNOT
    GROUP_SIZE_SWAP = GROUP_SIZE_SINGLE_QUBIT
    GROUP_SIZE = (
        GROUP_SIZE_SINGLE_QUBIT + GROUP_SIZE_CNOT + GROUP_SIZE_ISWAP + GROUP_SIZE_SWAP
    )

    assert GROUP_SIZE_SINGLE_QUBIT == 576
    assert GROUP_SIZE_CNOT == 5184
    assert GROUP_SIZE == 11_520

    @property
    def pauli_transfer_matrix(self) -> np.ndarray:
        if self.idx not in self._PTM_CACHE:
            if self.idx < 576:
                ptm = self.single_qubit_like_PTM(self.idx)
            elif self.idx < 576 + 5184:
                ptm = self.CNOT_like_PTM(self.idx - 576)
            elif self.idx < 576 + 2 * 5184:
                ptm = self.iSWAP_like_PTM(self.idx - (576 + 5184))
            else:  # GROUP_SIZE checked upon construction
                ptm = self.SWAP_like_PTM(self.idx - (576 + 2 * 5184))
            self._PTM_CACHE[self.idx] = ptm
        return self._PTM_CACHE[self.idx]

    @property
    def gate_decomposition(self):
        """
        Returns the gate decomposition of the two qubit Clifford group.

        Single qubit Cliffords are decomposed according to Epstein et al.
        """
        if self.idx not in self._GATE_DECOMP_CACHE:
            if self.idx < 576:
                gate_decomp = self.single_qubit_like_gates(self.idx)
            elif self.idx < 576 + 5184:
                gate_decomp = self.CNOT_like_gates(self.idx - 576)
            elif self.idx < 576 + 2 * 5184:
                gate_decomp = self.iSWAP_like_gates(self.idx - (576 + 5184))
            else:  # GROUP_SIZE checked upon construction
                gate_decomp = self.SWAP_like_gates(self.idx - (576 + 2 * 5184))
            self._GATE_DECOMP_CACHE[self.idx] = gate_decomp
        return self._GATE_DECOMP_CACHE[self.idx]

    @classmethod
    def single_qubit_like_PTM(cls, idx: int) -> np.ndarray:
        """
        Returns the pauli transfer matrix for gates of the single qubit like class
            (q0)  -- C1 --
            (q1)  -- C1 --
        """
        assert idx < cls.GROUP_SIZE_SINGLE_QUBIT
        idx_q0 = idx % 24
        idx_q1 = idx // 24
        pauli_transfer_matrix = np.kron(C1[idx_q1], C1[idx_q0])
        return pauli_transfer_matrix

    @classmethod
    def single_qubit_like_gates(cls, idx: int) -> List[Tuple[str, str]]:
        """
        Returns the gates for Cliffords of the single qubit like class
            (q0)  -- C1 --
            (q1)  -- C1 --
        """
        assert idx < cls.GROUP_SIZE_SINGLE_QUBIT
        idx_q0 = idx % 24
        idx_q1 = idx // 24

        g_q0 = [(g, "q0") for g in epstein_efficient_decomposition[idx_q0]]
        g_q1 = [(g, "q1") for g in epstein_efficient_decomposition[idx_q1]]
        gates = g_q0 + g_q1
        return gates

    @classmethod
    def CNOT_like_PTM(cls, idx: int) -> np.ndarray:
        """
        Returns the pauli transfer matrix for gates of the cnot like class
            (q0)  --C1--•--S1--      --C1--•--S1------
                        |        ->        |
            (q1)  --C1--⊕--S1--      --C1--•--S1^Y90--
        """
        assert idx < cls.GROUP_SIZE_CNOT
        idx_0 = idx % 24
        idx_1 = (idx // 24) % 24
        idx_2 = (idx // 576) % 3
        idx_3 = idx // 1728

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
        assert idx < cls.GROUP_SIZE_CNOT
        idx_0 = idx % 24
        idx_1 = (idx // 24) % 24
        idx_2 = (idx // 576) % 3
        idx_3 = idx // 1728

        C1_q0 = [(g, "q0") for g in epstein_efficient_decomposition[idx_0]]
        C1_q1 = [(g, "q1") for g in epstein_efficient_decomposition[idx_1]]
        CZ = [("CZ", ["q0", "q1"])]

        idx_2s = SingleQubitClifford.find_clifford_index(S1[idx_2])
        S1_q0 = [(g, "q0") for g in epstein_efficient_decomposition[idx_2s]]
        idx_3s = SingleQubitClifford.find_clifford_index(np.dot(C1[idx_3], Y90))
        S1_yq1 = [(g, "q1") for g in epstein_efficient_decomposition[idx_3s]]

        gates = C1_q0 + C1_q1 + CZ + S1_q0 + S1_yq1
        return gates

    @classmethod
    def iSWAP_like_PTM(cls, idx: int) -> np.ndarray:
        """
        Returns the pauli transfer matrix for gates of the iSWAP like class
            (q0)  --C1--*--S1--     --C1--•---Y90--•--S1^Y90--
                        |       ->        |        |
            (q1)  --C1--*--S1--     --C1--•--mY90--•--S1^X90--
        """
        assert idx < cls.GROUP_SIZE_ISWAP
        idx_0 = idx % 24
        idx_1 = (idx // 24) % 24
        idx_2 = (idx // 576) % 3
        idx_3 = idx // 1728

        C1_q0 = np.kron(np.eye(4), C1[idx_0])
        C1_q1 = np.kron(C1[idx_1], np.eye(4))
        # CZ
        sq_swap_gates = np.kron(mY90, Y90)
        # CZ
        S1_q0 = np.kron(np.eye(4), np.dot(S1[idx_2], Y90))
        S1y_q1 = np.kron(np.dot(C1[idx_3], X90), np.eye(4))

        return np.linalg.multi_dot(
            list(reversed([C1_q0, C1_q1, CZ, sq_swap_gates, CZ, S1_q0, S1y_q1]))
        )

    @classmethod
    def iSWAP_like_gates(cls, idx: int):
        """
        Returns the gates for Cliffords of the iSWAP like class
            (q0)  --C1--*--S1--     --C1--•---Y90--•--S1^Y90--
                        |       ->        |        |
            (q1)  --C1--*--S1--     --C1--•--mY90--•--S1^X90--
        """
        assert idx < cls.GROUP_SIZE_ISWAP
        idx_0 = idx % 24
        idx_1 = (idx // 24) % 24
        idx_2 = (idx // 576) % 3
        idx_3 = idx // 1728

        C1_q0 = [(g, "q0") for g in epstein_efficient_decomposition[idx_0]]
        C1_q1 = [(g, "q1") for g in epstein_efficient_decomposition[idx_1]]
        CZ = [("CZ", ["q0", "q1"])]

        sqs_idx_q0 = SingleQubitClifford.find_clifford_index(Y90)
        sqs_idx_q1 = SingleQubitClifford.find_clifford_index(mY90)
        sq_swap_gates_q0 = [
            (g, "q0") for g in epstein_efficient_decomposition[sqs_idx_q0]
        ]
        sq_swap_gates_q1 = [
            (g, "q1") for g in epstein_efficient_decomposition[sqs_idx_q1]
        ]

        idx_2s = SingleQubitClifford.find_clifford_index(np.dot(S1[idx_2], Y90))
        S1_q0 = [(g, "q0") for g in epstein_efficient_decomposition[idx_2s]]
        idx_3s = SingleQubitClifford.find_clifford_index(np.dot(C1[idx_3], X90))
        S1y_q1 = [(g, "q1") for g in epstein_efficient_decomposition[idx_3s]]

        gates = (
            C1_q0
            + C1_q1
            + CZ
            + sq_swap_gates_q0
            + sq_swap_gates_q1
            + CZ
            + S1_q0
            + S1y_q1
        )
        return gates

    @classmethod
    def SWAP_like_PTM(cls, idx: int) -> np.ndarray:
        """
        Returns the pauli transfer matrix for gates of the SWAP like class

        (q0)  --C1--x--     --C1--•-mY90--•--Y90--•-------
                    |   ->        |       |       |
        (q1)  --C1--x--     --C1--•--Y90--•-mY90--•--Y90--
        """
        assert idx < cls.GROUP_SIZE_SWAP
        idx_q0 = idx % 24
        idx_q1 = idx // 24
        sq_like_cliff = np.kron(C1[idx_q1], C1[idx_q0])
        sq_swap_gates_0 = np.kron(Y90, mY90)
        sq_swap_gates_1 = np.kron(mY90, Y90)
        sq_swap_gates_2 = np.kron(Y90, np.eye(4))

        return np.linalg.multi_dot(
            list(
                reversed(
                    [
                        sq_like_cliff,
                        CZ,
                        sq_swap_gates_0,
                        CZ,
                        sq_swap_gates_1,
                        CZ,
                        sq_swap_gates_2,
                    ]
                )
            )
        )

    @classmethod
    def SWAP_like_gates(cls, idx: int):
        """
        Returns the gates for Cliffords of the SWAP like class

        (q0)  --C1--x--     --C1--•-mY90--•--Y90--•-------
                    |   ->        |       |       |
        (q1)  --C1--x--     --C1--•--Y90--•-mY90--•--Y90--
        """
        assert idx < cls.GROUP_SIZE_SWAP
        idx_q0 = idx % 24
        idx_q1 = idx // 24
        C1_q0 = [(g, "q0") for g in epstein_efficient_decomposition[idx_q0]]
        C1_q1 = [(g, "q1") for g in epstein_efficient_decomposition[idx_q1]]
        CZ = [("CZ", ["q0", "q1"])]

        sqs_idx_q0 = SingleQubitClifford.find_clifford_index(mY90)
        sqs_idx_q1 = SingleQubitClifford.find_clifford_index(Y90)
        sq_swap_gates_0_q0 = [
            (g, "q0") for g in epstein_efficient_decomposition[sqs_idx_q0]
        ]
        sq_swap_gates_0_q1 = [
            (g, "q1") for g in epstein_efficient_decomposition[sqs_idx_q1]
        ]

        sqs_idx_q0 = SingleQubitClifford.find_clifford_index(Y90)
        sqs_idx_q1 = SingleQubitClifford.find_clifford_index(mY90)
        sq_swap_gates_1_q0 = [
            (g, "q0") for g in epstein_efficient_decomposition[sqs_idx_q0]
        ]
        sq_swap_gates_1_q1 = [
            (g, "q1") for g in epstein_efficient_decomposition[sqs_idx_q1]
        ]

        sqs_idx_q1 = SingleQubitClifford.find_clifford_index(Y90)
        sq_swap_gates_2_q0 = [(g, "q0") for g in epstein_efficient_decomposition[0]]
        sq_swap_gates_2_q1 = [
            (g, "q1") for g in epstein_efficient_decomposition[sqs_idx_q1]
        ]

        gates = (
            C1_q0
            + C1_q1
            + CZ
            + sq_swap_gates_0_q0
            + sq_swap_gates_0_q1
            + CZ
            + sq_swap_gates_1_q0
            + sq_swap_gates_1_q1
            + CZ
            + sq_swap_gates_2_q0
            + sq_swap_gates_2_q1
        )
        return gates
