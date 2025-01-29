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

import re
from typing import List


def parse_input_qubits(qubit_str: str) -> List[str]:
    """
    This generates a list of qubits from an unstructured input string.

    Args:
        qubit_str: Qubit input string, see examples for more information

    Examples:
        Enter qubits in a list format:
        >>> parse_input_qubits("q01,q02,q03,q04")
        >>> ["q01", "q02", "q03", "q04"]

        Enter qubit ranges:
        >>> parse_input_qubits("q01-q03")
        >>> ["q01", "q02", "q03"]

        Enter a mix of lists and ranges:
        >>> parse_input_qubits("q01-q05, q08, q10, q12-q15")
        >>> ["q01", "q02", "q03", "q04", "q05", "q08", "q10", "q12", "q13", "q14", "q15"]

    Returns:
        List of qubits ["qXX", ...]

    """
    # Split by commas or spaces while allowing for ranges
    tokens = re.split(r",\s*|\s+", qubit_str.strip())

    result = []

    for token in tokens:
        if "-" in token:
            # Handle ranges
            start, end = token.split("-")
            prefix = re.match(r"[a-zA-Z]+", start).group()
            start_num = int(re.search(r"\d+", start).group())
            end_num = int(re.search(r"\d+", end).group())

            # Adjust if start is greater than end
            if start_num > end_num:
                start_num, end_num = end_num, start_num

            result.extend([f"{prefix}{i:02}" for i in range(start_num, end_num + 1)])
        elif len(token) > 0:
            # Handle individual items
            result.append(token.strip())

    # Ensure unique values and return in sorted order
    return sorted(set(result), key=lambda x: (x[:2], int(x[2:])))
