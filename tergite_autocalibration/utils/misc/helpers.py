# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from typing import List


def generate_n_qubit_list(n_qubits: int, starting_from: int = 1) -> List[str]:
    """
    This generates a list of qubits.

    Args:
        n_qubits: The number of qubits.
        starting_from: Start counting from when numbering the qubits (default: 1).

    Returns:
        List of qubits ["qXX", ...] starting with "q01" (default, regulated by starting_from parameter).
    """
    return [f"q{i:02}" for i in range(starting_from, starting_from + n_qubits)]
