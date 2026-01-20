# This code is part of Tergite
#
# (C) Eleftherios Moschandreou 2024, 2025
# (C) Copyright Chalmers Next Labs 2024, 2025
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
from scipy.stats import truncnorm

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
    # iq_values = iq_values - (centroid_i + 1j * centroid_q)
    # iq_values = xr.apply_ufunc(lambda x: (np.angle(x, deg=True) + 360) % 360, iq_values)

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

    shots_between_1_2 = int(probabilities[state_between_1_and_2] * loops)
    shots_between_2_3 = int(probabilities[state_between_2_and_3] * loops)
    shots_between_3_1 = loops - shots_between_1_2 - shots_between_2_3

    angle_spread_in_deg = 10
    radius_spread_in_mV = 0.1
    mean_radius_in_mV = 1
    rng = np.random.default_rng()
    truncated_min_12 = (angle_1 - mean_angle_between_1_and_2) / angle_spread_in_deg
    truncated_max_12 = (angle_2 - mean_angle_between_1_and_2) / angle_spread_in_deg
    rv_12 = truncnorm(
        truncated_min_12,
        truncated_max_12,
        loc=mean_angle_between_1_and_2,
        scale=angle_spread_in_deg,
    )
    iq_angles_12 = rv_12.rvs(size=shots_between_1_2)
    iq_angles_12_rad = np.deg2rad(iq_angles_12)
    iq_magnitudes_12 = rng.normal(
        mean_radius_in_mV, radius_spread_in_mV, shots_between_1_2
    )
    i_12 = iq_magnitudes_12 * np.cos(iq_angles_12_rad)
    q_12 = iq_magnitudes_12 * np.sin(iq_angles_12_rad)

    truncated_min_23 = (angle_2 - mean_angle_between_2_and_3) / angle_spread_in_deg
    truncated_max_23 = (angle_3 - mean_angle_between_2_and_3) / angle_spread_in_deg
    rv_23 = truncnorm(
        truncated_min_23,
        truncated_max_23,
        loc=mean_angle_between_2_and_3,
        scale=angle_spread_in_deg,
    )
    iq_angles_23 = rv_23.rvs(size=shots_between_2_3)
    iq_angles_23_rad = np.deg2rad(iq_angles_23)
    iq_magnitudes_23 = rng.normal(
        mean_radius_in_mV, radius_spread_in_mV, shots_between_2_3
    )
    i_23 = iq_magnitudes_23 * np.cos(iq_angles_23_rad)
    q_23 = iq_magnitudes_23 * np.sin(iq_angles_23_rad)

    truncated_min_31 = (angle_3 - mean_angle_between_3_and_1) / angle_spread_in_deg
    truncated_max_31 = (angle_1 - mean_angle_between_3_and_1) / angle_spread_in_deg
    rv_31 = truncnorm(
        truncated_min_31,
        truncated_max_31,
        loc=mean_angle_between_3_and_1,
        scale=angle_spread_in_deg,
    )
    iq_angles_31 = rv_31.rvs(size=shots_between_3_1)
    iq_angles_31_rad = np.deg2rad(iq_angles_31)
    iq_magnitudes_31 = rng.normal(
        mean_radius_in_mV, radius_spread_in_mV, shots_between_3_1
    )
    i_31 = iq_magnitudes_31 * np.cos(iq_angles_31_rad)
    q_31 = iq_magnitudes_31 * np.sin(iq_angles_31_rad)

    return assigned_states
