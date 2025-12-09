# This code is part of Tergite
#
# Copyright (C) Pontus Vikstål 2025
# Copyright (C) Chalmers Next Labs 2025

import unittest
import numpy as np

from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.randomized_benchmarking import (
    randomized_benchmarking_sequence,
    calculate_net_clifford,
)
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.pauli_transfer_matrices import (
    CZ,
    I,
    X_theta,
    Y_theta,
)
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.clifford_group import (
    SingleQubitClifford,
    TwoQubitClifford,
)


class TestRandomizedBenchmarkingSequence(unittest.TestCase):

    def setUp(self) -> None:
        # CliffordClass, clifford_group, interleaved_clifford_idx
        self.test_cases = [(SingleQubitClifford, 1, 20), (TwoQubitClifford, 2, 10_4368)]

    def test_recovery_clifford_produces_identity(self):
        """Test that recovery gate in clifford sequence yields identity."""
        for CliffordClass, clifford_group, _ in self.test_cases:
            with self.subTest(CliffordClass=CliffordClass.__name__):
                sequence = randomized_benchmarking_sequence(
                    number_of_cliffords=100,
                    apply_inverse=True,
                    clifford_group=clifford_group,
                    seed=123,
                )
                # Get the recovery Clifford
                recovery_clifford = CliffordClass(sequence[-1])
                # Compute net Clifford from the sequence
                net_clifford = calculate_net_clifford(sequence[:-1], CliffordClass)
                # Compute the product of the net clifford and the recovery clifford
                clifford = net_clifford * recovery_clifford
                self.assertTrue(
                    clifford == CliffordClass(0),
                    "The product of a single-qubit sequence and its recovery should be the identity",
                )

    def test_interleaved_randomized_benchmarking(self):
        """Test that recovery gate in clifford sequence yields identity."""
        for CliffordClass, clifford_group, interleaved_clifford_idx in self.test_cases:
            with self.subTest(CliffordClass=CliffordClass.__name__):
                sequence = randomized_benchmarking_sequence(
                    number_of_cliffords=100,
                    apply_inverse=True,
                    clifford_group=clifford_group,
                    interleaved_clifford_idx=interleaved_clifford_idx,
                    seed=123,
                )
                # Get the recovery Clifford
                recovery_clifford = CliffordClass(sequence[-1])
                # Compute net Clifford from the sequence
                net_clifford = calculate_net_clifford(sequence[:-1], CliffordClass)
                # Compute the product of the net clifford and the recovery clifford
                clifford = net_clifford * recovery_clifford
                self.assertTrue(
                    clifford == CliffordClass(0),
                    "The product of a single-qubit sequence and its recovery should be the identity",
                )

    def test_interleaved_cz(self):
        """Test that interleaved randomized benchmarking with a CZ gate results in the identity PTM."""

        CliffordClass = TwoQubitClifford
        CZ_INDEX = 10_4368  # Clifford index for CZ

        sequence = randomized_benchmarking_sequence(
            number_of_cliffords=100,
            apply_inverse=True,
            clifford_group=2,
            interleaved_clifford_idx=CZ_INDEX,  # Clifford index for CZ
            seed=123,
        )

        # Map from gate names to their PTMs
        ptm_map = {
            "X180": X_theta(180),
            "X90": X_theta(90),
            "Y180": Y_theta(180),
            "Y90": Y_theta(90),
            "mX90": X_theta(-90),
            "mY90": Y_theta(-90),
            "CZ": CZ,
        }

        # Pre-compute the tensor products to avoid repeating calculations
        ptm_q0 = {gate: np.kron(I, ptm) for gate, ptm in ptm_map.items()}
        ptm_q1 = {gate: np.kron(ptm, I) for gate, ptm in ptm_map.items()}
        identity = np.kron(I, I)

        # Start with identity matrix
        net_ptm = identity

        for idx in sequence:
            if idx == CZ_INDEX:
                net_ptm = np.dot(CZ, net_ptm)
                continue

            decomposition = CliffordClass(idx).gate_decomposition
            if decomposition is None:
                raise ValueError(f"Clifford gate {idx} has no decomposition.")

            for gate, q in decomposition:
                if gate == "I":
                    continue
                elif gate == "CZ":
                    net_ptm = np.dot(CZ, net_ptm)
                else:
                    qubit_index = int(q[1:])
                    if qubit_index == 0:
                        net_ptm = np.dot(ptm_q0[gate], net_ptm)
                    elif qubit_index == 1:
                        net_ptm = np.dot(ptm_q1[gate], net_ptm)
                    else:
                        raise ValueError(f"Invalid qubit index {q} in decomposition.")

        # Verify result is close to identity
        phase = np.angle(net_ptm[0, 0])  # get global phase
        net_ptm = np.exp(-1j * phase) * net_ptm  # remove possible global phase
        np.testing.assert_array_almost_equal(net_ptm, identity, decimal=5)


if __name__ == "__main__":
    unittest.main()
