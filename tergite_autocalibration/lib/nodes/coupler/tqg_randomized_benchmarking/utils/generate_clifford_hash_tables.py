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

from os import mkdir
from os.path import join, dirname, abspath
from zlib import crc32

import numpy as np

from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.two_qubit_clifford_group import (
    SingleQubitClifford,
    TwoQubitClifford,
)
from tergite_autocalibration.utils.logging import logger

output_dir = join(abspath(dirname(__file__)), "clifford_hash_tables")
try:
    mkdir(output_dir)
except FileExistsError:
    pass


def construct_clifford_lookuptable(generator, indices):
    """ """
    lookuptable = []
    for idx in indices:
        clifford = generator(idx=idx)
        # important to use crc32 hashing as this is a non-random hash
        hash_val = crc32(clifford.pauli_transfer_matrix.round().astype(int))
        lookuptable.append(hash_val)
    return lookuptable


def generate_hash_tables():
    logger.info("Generating Clifford hash tables.")
    single_qubit_hash_lut = construct_clifford_lookuptable(
        SingleQubitClifford, np.arange(24)
    )
    with open(join(output_dir, "single_qubit_hash_lut.txt"), "w") as f:
        for h in single_qubit_hash_lut:
            f.write(str(h) + "\n")

    two_qubit_hash_lut = construct_clifford_lookuptable(
        TwoQubitClifford, np.arange(11520)
    )
    with open(join(output_dir, "two_qubit_hash_lut.txt"), "w") as f:
        for h in two_qubit_hash_lut:
            f.write(str(h) + "\n")
    logger.info("Successfully generated Clifford hash tables.")


if __name__ == "__main__":
    generate_hash_tables()
