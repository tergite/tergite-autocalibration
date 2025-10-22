# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2025
# (C) Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import re


def expand_range(s: str):
    # Example input: "q01-q11"
    starting_qubit, ending_qubit = s.split("-")

    # Extract prefix (letters, usually just q) and number part
    prefix_start, num_start = re.match(r"([a-zA-Z_]*)(\d+)", starting_qubit).groups()
    prefix_end, num_end = re.match(r"([a-zA-Z_]*)(\d+)", ending_qubit).groups()

    # Make sure the prefixes match
    if prefix_start != prefix_end:
        raise ValueError(f"Prefixes don't match: {prefix_start} vs {prefix_end}")

    # Convert to integers and preserve zero-padding
    n1, n2 = int(num_start), int(num_end)
    width = len(num_start)

    # Generate the list
    return [f"{prefix_start}{i:0{width}d}" for i in range(n1, n2 + 1)]


def split_range_input(input: str):
    module_nums = []
    # example input 1-3, 5, 6
    for part in input.split(","):
        part = part.strip()
        if "-" in part:
            start, end = map(int, part.split("-"))
            module_nums.extend(range(start, end + 1))
        else:
            module_nums.append(int(part))
    sorted_module_nums = sorted(set(module_nums))
    return sorted_module_nums
