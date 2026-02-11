# This code is part of Tergite
#
# (C) Eleftherios Moschandreou 2024, 2025, 2026
# (C) Copyright Chalmers Next Labs 2024, 2025, 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np
import xarray as xr

from tergite_autocalibration.config.globals import REDIS_CONNECTION


def assign_state(iq_values: xr.DataArray) -> xr.DataArray:
    qubit = iq_values.attrs["qubit"]
    redis_key = f"transmons:{qubit}"
    centroid_i = float(REDIS_CONNECTION.hget(f"{redis_key}", "centroid_I"))
    centroid_q = float(REDIS_CONNECTION.hget(f"{redis_key}", "centroid_Q"))
    omega_01 = float(REDIS_CONNECTION.hget(f"{redis_key}", "omega_01"))
    omega_12 = float(REDIS_CONNECTION.hget(f"{redis_key}", "omega_12"))
    omega_20 = float(REDIS_CONNECTION.hget(f"{redis_key}", "omega_20"))
    state_boundaries = {"01": omega_01, "12": omega_12, "20": omega_20}
    sorted_state_boundaries_dict = {
        k: v for k, v in sorted(state_boundaries.items(), key=lambda item: item[1])
    }
    sorted_state_boundaries = list(sorted_state_boundaries_dict.keys())
    iq_values = iq_values - (centroid_i + 1j * centroid_q)
    iq_values = xr.apply_ufunc(lambda x: (np.angle(x, deg=True) + 360) % 360, iq_values)

    def state_filter(angles_array) -> xr.DataArray:
        boundary_1 = sorted_state_boundaries[0]  # eg '01'
        boundary_2 = sorted_state_boundaries[1]  # eg '12'
        boundary_3 = sorted_state_boundaries[2]  # eg '20'
        angle_1 = state_boundaries[boundary_1]
        angle_2 = state_boundaries[boundary_2]
        angle_3 = state_boundaries[boundary_3]
        # find the common state between the boundaries. eg: '01' & '12' -> 1
        state_between_1_and_2 = int(list(set(boundary_1) & set(boundary_2))[0])
        state_between_2_and_3 = int(list(set(boundary_2) & set(boundary_3))[0])
        state_between_3_and_1 = int(list(set(boundary_3) & set(boundary_1))[0])
        condition_1 = (
            (angles_array > angle_1) & (angles_array < angle_2)
        ) * state_between_1_and_2
        condition_2 = (
            (angles_array > angle_2) & (angles_array < angle_3)
        ) * state_between_2_and_3
        condition_3 = (
            (angles_array < angle_1) | (angles_array > angle_3)
        ) * state_between_3_and_1
        return condition_1 + condition_2 + condition_3

    assigned_states = xr.apply_ufunc(state_filter, iq_values)
    return assigned_states


def calculate_probabilities(iq_data_var: xr.DataArray):
    if "loops" not in iq_data_var.coords:
        raise ValueError("Dataarray does not contain loop coordinate")
    states_array = assign_state(iq_data_var)
    qubit = iq_data_var.attrs["qubit"]
    loops_coord = iq_data_var.loops.name
    number_of_loops = iq_data_var.loops.size

    zeros = xr.where(states_array == 0, x=1, y=0)  # keep only |0> states
    ones = xr.where(states_array == 1, x=1, y=0)  # keep only |1> states
    twos = xr.where(states_array == 2, x=1, y=0)  # keep only |2> states

    ones = ones.reduce(func=np.sum, dim=loops_coord)
    twos = twos.reduce(func=np.sum, dim=loops_coord)
    zeros = zeros.reduce(func=np.sum, dim=loops_coord)

    probabilities_state_0 = zeros / number_of_loops
    probabilities_state_0 = probabilities_state_0.assign_coords(state=0)
    probabilities_state_0 = probabilities_state_0.assign_coords(qubit=qubit)
    probabilities_state_1 = ones / number_of_loops
    probabilities_state_1 = probabilities_state_1.assign_coords(state=1)
    probabilities_state_1 = probabilities_state_1.assign_coords(qubit=qubit)
    probabilities_state_2 = twos / number_of_loops
    probabilities_state_2 = probabilities_state_2.assign_coords(state=2)
    probabilities_state_2 = probabilities_state_2.assign_coords(qubit=qubit)

    state_probabilities = xr.concat(
        [probabilities_state_0, probabilities_state_1, probabilities_state_2],
        dim="state",
    )
    return state_probabilities


import matplotlib.pyplot as plt

fig, ax = plt.subplots(1, 1)


def generate_iq_shots(probabilities: np.ndarray, qubit: str, loops: int) -> np.ndarray:
    """
    given the probabilities array, generate an array of IQ points
    of size `loops` that given the loaded discriminator would
    produce the probabilities. This function is the reverse of
    calculate_probabilities and is used to create dummy datasets.
    Example of probabilities array: [0.2, 0.3, 0.5]
    """
    redis_key = f"transmons:{qubit}"
    centroid_i = float(REDIS_CONNECTION.hget(f"{redis_key}", "centroid_I"))
    centroid_q = float(REDIS_CONNECTION.hget(f"{redis_key}", "centroid_Q"))
    omega_01 = float(REDIS_CONNECTION.hget(f"{redis_key}", "omega_01"))
    omega_12 = float(REDIS_CONNECTION.hget(f"{redis_key}", "omega_12"))
    omega_20 = float(REDIS_CONNECTION.hget(f"{redis_key}", "omega_20"))

    state_boundaries = {"01": omega_01, "12": omega_12, "20": omega_20}
    sorted_state_boundaries_dict = {
        k: v for k, v in sorted(state_boundaries.items(), key=lambda item: item[1])
    }
    sorted_state_boundaries = list(sorted_state_boundaries_dict.keys())

    boundary_1 = sorted_state_boundaries[0]  # eg '01'
    boundary_2 = sorted_state_boundaries[1]  # eg '12'
    boundary_3 = sorted_state_boundaries[2]  # eg '20'
    # the important here is that angle_1, angle_2 and angle_3 are sorted
    # eg angle_1 = 45, angle_2 = 120, angle_3 = 300
    angle_1 = state_boundaries[boundary_1]
    angle_2 = state_boundaries[boundary_2]
    angle_3 = state_boundaries[boundary_3]

    # find the common state between the boundaries. eg: '01' & '12' -> 1
    state_between_1_and_2 = int(list(set(boundary_1) & set(boundary_2))[0])
    state_between_2_and_3 = int(list(set(boundary_2) & set(boundary_3))[0])
    state_between_3_and_1 = int(list(set(boundary_3) & set(boundary_1))[0])

    mean_angle_between_1_and_2 = (angle_1 + angle_2) / 2
    mean_angle_between_2_and_3 = (angle_2 + angle_3) / 2
    mean_angle_between_3_and_1 = (angle_3 + angle_1) / 2 + 180

    mean_angles_dict = {
        state_between_1_and_2: mean_angle_between_1_and_2,
        state_between_2_and_3: mean_angle_between_2_and_3,
        state_between_3_and_1: mean_angle_between_3_and_1,
    }

    number_of_pixels = probabilities.size // 3
    probabilities = probabilities.T.reshape(number_of_pixels, 3)

    angle_spread_in_deg = 1
    radius_spread_in_mV = 0.1
    mean_radius_in_mV = 2
    rng = np.random.default_rng()
    angles = np.array([])
    for _ in range(loops):
        for pixel_probs in probabilities:
            state = np.random.choice([0, 1, 2], p=pixel_probs)
            # TODO: for more realistic, draw angle from normal distribution
            angle = mean_angles_dict[state]
            angles = np.append(angles, angle)
    magnitudes = rng.normal(
        mean_radius_in_mV, radius_spread_in_mV, size=number_of_pixels
    )
    all_angles_rad = np.deg2rad(angles)
    all_magnitudes = np.tile(magnitudes, loops)
    i = all_magnitudes * np.cos(all_angles_rad)
    q = all_magnitudes * np.sin(all_angles_rad)
    complex_iq = i + 1j * q
    iq_points = complex_iq + centroid_i + 1j * centroid_q

    return iq_points
