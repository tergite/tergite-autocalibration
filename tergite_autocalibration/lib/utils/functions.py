# This code is part of Tergite
#
# (C) Copyright Joel Sandås 2024
# (C) Copyright Eleftherios Moschandreou 2025
# (C) Copyright Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


def exponential_decay_function(m: float, p: float, A: float, B: float) -> float:
    """
    Exponential decay function.
    :param m: Exponent base.
    :param p: Decay factor.
    :param A: Amplitude.
    :param B: Offset.
    :return: Result of the exponential decay function.
    """
    return A * p**m + B


def isosceles_triangle(
    base_length: float = 0.002, height: float = 0.003, center: tuple = (0, 0)
) -> tuple:
    """
    Returns the coordinates of three points defining an isosceles triangle.

    Parameters:
        base_length (float): Length of the base of the triangle.
        height (float): Height from base to apex.
        center (tuple): (x, y) coordinates of the midpoint of the base.

    Returns:
        tuple: Three coordinate pairs (base_left, base_right, apex).
    """
    cx, cy = center
    half_base = base_length / 2

    base_left = (cx - half_base, cy)
    base_right = (cx + half_base, cy)
    apex = (cx, cy + height)

    return base_left, base_right, apex
