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
from typing import Literal

I = np.eye(4)

# Pauli group
X = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, -1]], dtype=int)
Y = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]], dtype=int)
Z = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]], dtype=int)

# Exchange group
S = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 1, 0, 0], [0, 0, 1, 0]], dtype=int)
S2 = np.dot(S, S)

# Hadamard group
H = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, -1, 0], [0, 1, 0, 0]], dtype=int)

# CZ
CZ = np.array(
    [
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    ],
    dtype=int,
)


def X_theta(theta: float, unit: Literal["deg", "rad"] = "deg") -> np.ndarray:
    """
    Return the Pauli Transfer Matrix (PTM) of a rotation of angle theta
    around the X-axis.

    Args:
        theta (float): Rotation angle.
        unit (str): Unit of the angle, either "deg" for degrees or "rad" for radians.

    Returns:
        np.ndarray: The 4x4 PTM matrix corresponding to the X rotation.
    """
    if unit == "deg":
        theta = np.deg2rad(theta)
    elif unit != "rad":
        raise ValueError(f"Unsupported unit '{unit}'. Use 'deg' or 'rad'.")

    cos = np.cos(theta)
    sin = np.sin(theta)

    X = np.array(
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, cos, -sin],
            [0, 0, sin, cos],
        ],
        dtype=np.float64,
    )
    return X


def Y_theta(theta: float, unit: Literal["deg", "rad"] = "deg") -> np.ndarray:
    """
    Return the Pauli Transfer Matrix (PTM) of a rotation of angle theta
    around the Y-axis.

    Args:
        theta (float): Rotation angle.
        unit (str): Unit of the angle, either "deg" for degrees or "rad" for radians.

    Returns:
        np.ndarray: The 4x4 PTM matrix corresponding to the Y rotation.
    """
    if unit == "deg":
        theta = np.deg2rad(theta)
    elif unit != "rad":
        raise ValueError(f"Unsupported unit '{unit}'. Use 'deg' or 'rad'.")

    cos = np.cos(theta)
    sin = np.sin(theta)

    Y = np.array(
        [
            [1, 0, 0, 0],
            [0, cos, 0, sin],
            [0, 0, 1, 0],
            [0, -sin, 0, cos],
        ],
        dtype=np.float64,
    )
    return Y
