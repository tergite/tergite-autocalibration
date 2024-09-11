# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
# (C) Copyright Tong Liu 2023
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

# TODO
# ******************************************************
# This not a good implementation. better create a  *****
# Clifford object with the physical decompositions *****
# and the PTM representation as attributes         *****
# ******************************************************

XY_decompositions = [{}] * 24

XY_decompositions[0] = {
    "1": {"theta": 0, "phi": 0},
}

XY_decompositions[1] = {
    "1": {"theta": 90, "phi": 90},
    "2": {"theta": 90, "phi": 0},
}

XY_decompositions[2] = {
    "1": {"theta": -90, "phi": 0},
    "2": {"theta": -90, "phi": 90},
}

XY_decompositions[3] = {
    "1": {"theta": 180, "phi": 0},
}

XY_decompositions[4] = {
    "1": {"theta": -90, "phi": 90},
    "2": {"theta": -90, "phi": 0},
}

XY_decompositions[5] = {
    "1": {"theta": 90, "phi": 0},
    "2": {"theta": -90, "phi": 90},
}

XY_decompositions[6] = {
    "1": {"theta": 180, "phi": 90},
}

XY_decompositions[7] = {
    "1": {"theta": -90, "phi": 90},
    "2": {"theta": 90, "phi": 0},
}

XY_decompositions[8] = {
    "1": {"theta": 90, "phi": 0},
    "2": {"theta": 90, "phi": 90},
}

XY_decompositions[9] = {
    "1": {"theta": 180, "phi": 0},
    "2": {"theta": 180, "phi": 90},
}

XY_decompositions[10] = {
    "1": {"theta": 90, "phi": 90},
    "2": {"theta": -90, "phi": 0},
}

XY_decompositions[11] = {
    "1": {"theta": -90, "phi": 0},
    "2": {"theta": 90, "phi": 90},
}

XY_decompositions[12] = {
    "1": {"theta": 90, "phi": 90},
    "2": {"theta": 180, "phi": 0},
}

XY_decompositions[13] = {
    "1": {"theta": -90, "phi": 0},
}

XY_decompositions[14] = {
    "1": {"theta": 90, "phi": 0},
    "2": {"theta": -90, "phi": 90},
    "3": {"theta": -90, "phi": 0},
}

XY_decompositions[15] = {
    "1": {"theta": -90, "phi": 90},
}

XY_decompositions[16] = {
    "1": {"theta": 90, "phi": 0},
}

XY_decompositions[17] = {
    "1": {"theta": 90, "phi": 0},
    "2": {"theta": 90, "phi": 90},
    "3": {"theta": 90, "phi": 0},
}

XY_decompositions[18] = {
    "1": {"theta": -90, "phi": 90},
    "2": {"theta": 180, "phi": 0},
}

XY_decompositions[19] = {
    "1": {"theta": 90, "phi": 0},
    "2": {"theta": 180, "phi": 90},
}

XY_decompositions[20] = {
    "1": {"theta": 90, "phi": 0},
    "2": {"theta": -90, "phi": 90},
    "3": {"theta": 90, "phi": 0},
}

XY_decompositions[21] = {
    "1": {"theta": 90, "phi": 90},
}

XY_decompositions[22] = {
    "1": {"theta": -90, "phi": 0},
    "2": {"theta": 180, "phi": 90},
}

XY_decompositions[23] = {
    "1": {"theta": 90, "phi": 0},
    "2": {"theta": 90, "phi": 90},
    "3": {"theta": -90, "phi": 0},
}


def x_PTM(theta: float):
    theta = np.deg2rad(theta)
    if np.abs(np.abs(theta) - np.pi) < 1e-6 or np.abs(np.abs(theta) - np.pi / 2) < 1e-6:
        cos = round(np.cos(theta))
        sin = round(np.sin(theta))
        matrix = np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, cos, -sin], [0, 0, sin, cos]]
        )
    else:
        raise ValueError("Invalid angle")
    return matrix


def y_PTM(theta: float):
    theta = np.deg2rad(theta)
    # print(phi)
    if np.abs(np.abs(theta) - np.pi) < 1e-6 or np.abs(np.abs(theta) - np.pi / 2) < 1e-6:
        cos = round(np.cos(theta))
        sin = round(np.sin(theta))
        matrix = np.array(
            [[1, 0, 0, 0], [0, cos, 0, sin], [0, 0, 1, 0], [0, -sin, 0, cos]]
        )
    else:
        raise ValueError("Invalid angle")
    return matrix


def RXY(theta: float, phi: float):
    theta = np.deg2rad(theta)
    phi = np.deg2rad(phi)
    rotation = np.array(
        [
            [np.cos(theta / 2), -1j * np.exp(-1j * phi) * np.sin(theta / 2)],
            [-1j * np.exp(1j * phi) * np.sin(theta / 2), np.cos(theta / 2)],
        ]
    )
    return rotation


def from_physical_decomp_to_PTM(physical_decomp: dict):
    matrix = np.identity(4, dtype=np.int64)
    for operation in physical_decomp.values():
        # print(operation)
        theta = operation["theta"]
        phi = operation["phi"]
        if theta == 0 and phi == 0:
            return matrix
        if phi == 0:
            ptm = x_PTM(theta)
            matrix = np.matmul(ptm, matrix, dtype=np.int64)
        elif phi == 90:
            ptm = y_PTM(theta)
            matrix = np.matmul(ptm, matrix, dtype=np.int64)
    return matrix


def is_sequence_identity(rng_sequence: np.ndarray) -> bool:
    matrix = np.identity(2)
    for rng_i in rng_sequence:
        this_decomposition = XY_decompositions[rng_i]
        for operation in this_decomposition.values():
            theta = operation["theta"]
            phi = operation["phi"]
            matrix = np.matmul(RXY(theta, phi), matrix)
    # check if the total operation produces I or -I
    print(f"{ np.allclose(matrix,  np.identity(2)) = }")
    print(f"{ np.allclose(matrix, -np.identity(2)) = }")
    return np.allclose(matrix, np.identity(2)) or np.allclose(matrix, -np.identity(2))


def reversing_XY_matrix(rng_sequence):
    product_matrix = np.identity(4, dtype=np.int64)
    for rng in rng_sequence:
        physical_decomp = XY_decompositions[rng]
        ptm = from_physical_decomp_to_PTM(physical_decomp)
        product_matrix = np.matmul(ptm, product_matrix, dtype=np.int64)

    for decomp in XY_decompositions:
        ptm = from_physical_decomp_to_PTM(decomp)
        if np.array_equal(product_matrix, ptm):
            equivalent_ptm = ptm
            # print(f'{ equivalent_ptm = }')
            reversing_matrix = np.linalg.inv(equivalent_ptm).astype(np.int64)

    for i, decomp in enumerate(XY_decompositions):
        ptm = from_physical_decomp_to_PTM(decomp)
        if np.array_equal(reversing_matrix, ptm):
            reversing_index = i

    reversing_decomposition = XY_decompositions[reversing_index]
    return reversing_index, reversing_decomposition


# ---
if __name__ == "__main__":
    test_sequence = np.array(np.random.randint(0, 24, 10), dtype=np.int32)
    reversing_index, _ = reversing_XY_matrix(test_sequence)
    print(f"{ test_sequence = }")
    print(f"{ reversing_index = }")
    sequence = np.append(test_sequence, reversing_index)

    is_sequence_identity(sequence)
