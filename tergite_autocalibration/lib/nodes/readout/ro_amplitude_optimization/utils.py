# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2025
# (C) Copyright Chalemers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np


def align_on_y_axis(
    iq_points: np.ndarray,
    classified_states: np.ndarray,
    boundary_angle_rad: float,
    absolute_threshold: float,
    zero_state_index=0,
    first_state_index=1,
) -> tuple[np.ndarray, float, float]:
    """
    Translate and rotate the IQ samples so that all the |0> are on the I<0 semi-plane
    and all the |1> states are on the I>0 semi plane in accordance to Quantify Scheduler
    convention for Thresholded Acquisitions
    """
    rotation_angle_rad = np.pi / 2 - boundary_angle_rad
    rotation_matrix = np.array(
        [
            [np.cos(rotation_angle_rad), -np.sin(rotation_angle_rad)],
            [np.sin(rotation_angle_rad), np.cos(rotation_angle_rad)],
        ]
    )
    mirror_rotation = np.array(
        [
            [np.cos(np.pi), -np.sin(np.pi)],
            [np.sin(np.pi), np.cos(np.pi)],
        ]
    )
    # translated_IQ = iq_points - np.array([0, y_intercept])
    translated_IQ = iq_points
    rotated_IQ = translated_IQ @ rotation_matrix.T

    rotated_IQ0 = rotated_IQ[classified_states == zero_state_index]
    rotated_IQ1 = rotated_IQ[classified_states == first_state_index]
    center_of_rotated_I_0 = np.mean(rotated_IQ0[:, 0])
    center_of_rotated_I_1 = np.mean(rotated_IQ1[:, 0])
    if center_of_rotated_I_0 > center_of_rotated_I_1:
        rotation_angle_rad = rotation_angle_rad + np.pi
        rotated_IQ = rotated_IQ @ mirror_rotation.T

    rotated_IQ0 = rotated_IQ[classified_states == zero_state_index]
    rotated_IQ1 = rotated_IQ[classified_states == first_state_index]
    center_of_rotated_I_0 = np.mean(rotated_IQ0[:, 0])
    center_of_rotated_I_1 = np.mean(rotated_IQ1[:, 0])

    # FIXME: that first if is due to the 2- not2 thresholding. better trigonometry can simplify this
    # FIXME: if this message is still here keep an eye on the rotated thresholds
    if (
        center_of_rotated_I_0
        < -absolute_threshold
        < absolute_threshold
        < center_of_rotated_I_1
    ):
        if (
            absolute_threshold - center_of_rotated_I_0
            < -absolute_threshold - center_of_rotated_I_0
        ):
            threshold = absolute_threshold
        else:
            threshold = -absolute_threshold
    elif center_of_rotated_I_0 < absolute_threshold < center_of_rotated_I_1:
        threshold = absolute_threshold
    else:
        threshold = -absolute_threshold

    if not center_of_rotated_I_0 < threshold < center_of_rotated_I_1:
        raise ValueError("threshold is at an imporoper value")

    return rotated_IQ, rotation_angle_rad, threshold
