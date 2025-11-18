# This code is part of Tergite
#
# Copyright (C) Pontus Vikstål 2025
# Copyright (C) Chalmers Next Labs 2025

import unittest
import numpy as np
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.clifford_group import (
    SingleQubitClifford,
    TwoQubitClifford,
)


class TestClifford(unittest.TestCase):

    def setUp(self):
        # Clear caches before tests
        SingleQubitClifford.CLIFFORD_HASH_TABLE.clear()
        TwoQubitClifford.CLIFFORD_HASH_TABLE.clear()
        TwoQubitClifford._PTM_CACHE.clear()
        TwoQubitClifford._GATE_DECOMP_CACHE.clear()

        # Define test cases as CliffordClass
        self.test_cases = [SingleQubitClifford, TwoQubitClifford]

    def test_clifford_equality(self):
        for CliffordClass in self.test_cases:
            with self.subTest(CliffordClass=CliffordClass.__name__):
                c1 = CliffordClass(5)
                c2 = CliffordClass(5)
                c3 = CliffordClass(6)

                self.assertEqual(
                    c1,
                    c2,
                    f"{CliffordClass.__name__}s with the same index should be equal",
                )
                self.assertNotEqual(
                    c1,
                    c3,
                    f"{CliffordClass.__name__}s with different indices should not be equal",
                )

    def test_identity_clifford(self):
        for CliffordClass in self.test_cases:
            with self.subTest(CliffordClass=CliffordClass.__name__):
                ptm = CliffordClass(0).pauli_transfer_matrix
                size = ptm.shape[0]
                eye = np.identity(size)
                self.assertTrue(
                    np.array_equal(eye, ptm),
                    f"The identity {CliffordClass.__name__} should have an identity PTM",
                )

    def test_get_inverse(self):
        for CliffordClass in self.test_cases:
            with self.subTest(CliffordClass=CliffordClass.__name__):
                idx = 10  # arbitrary index
                c = CliffordClass(idx)
                c_inv = c.get_inverse()
                # Check that the inverse is correct up to a global-phase
                c_eye = c_inv * c  # this should be the identity
                eye = CliffordClass(0)  # This should be the identity
                self.assertTrue(
                    c_eye == eye,
                    f"The product of a {CliffordClass.__name__} and its inverse should be the identity",
                )

    def test_two_qubit_clifford_caching(self):
        """Test that the PTM and gate decomposition caches are shared between instances.
        This is only used for TwoQubitClifford, as SingleQubitClifford does not have a cache.
        """
        CliffordClass = TwoQubitClifford

        idx1, idx2 = 3, 5  # arbitrary indices

        # Compute PTMs
        c1_ptm = CliffordClass(idx=idx1).pauli_transfer_matrix
        self.assertIn(idx1, CliffordClass._PTM_CACHE)
        np.testing.assert_array_equal(c1_ptm, CliffordClass._PTM_CACHE[idx1])

        # Check that the instances share the same cache
        c2 = CliffordClass(idx=idx2)
        np.testing.assert_array_equal(c2._PTM_CACHE[idx1], c1_ptm)

        # Compute gate decomposition
        decomp1 = CliffordClass(idx=idx1).gate_decomposition
        self.assertIn(idx1, CliffordClass._GATE_DECOMP_CACHE)
        self.assertEqual(decomp1, CliffordClass._GATE_DECOMP_CACHE[idx1])

        # Check that a new instance shares the same cache
        decomp2 = CliffordClass(idx=idx2)
        self.assertEqual(decomp2._GATE_DECOMP_CACHE[idx1], decomp1)

    def test_hash_table_generation(self):
        for CliffordClass in self.test_cases:
            with self.subTest(CliffordClass=CliffordClass.__name__):
                idx = 5  # Some arbitrary Clifford idx
                c = CliffordClass(idx)
                ptm = c.pauli_transfer_matrix

                # Trigger hash table population
                c.find_clifford_index(ptm)

                # Check if the hash table was correctly populated
                hash_value = c._hash_matrix(ptm)
                # Assert that the hash value is in the hash table
                self.assertIn(hash_value, CliffordClass.CLIFFORD_HASH_TABLE)
                # Assert that the index in the hash table matches the original index
                self.assertEqual(CliffordClass.CLIFFORD_HASH_TABLE[hash_value], idx)


if __name__ == "__main__":
    unittest.main()
