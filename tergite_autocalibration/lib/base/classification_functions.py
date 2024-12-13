import numpy as np
import xarray as xr

from tergite_autocalibration.config.settings import REDIS_CONNECTION


def assign_state(qubit: str, iq_values: np.ndarray) -> xr.DataArray:
    """
    takes as input the array of iq points. Loads the three boundaries from
    redis and classifies each iq point to the corresponding state
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
    # translated iq_values so the their origin is the centroid
    iq_values_translated = iq_values - (centroid_i + 1j * centroid_q)
    # covert the translated iq to an array of angles with respect to the centroid
    iq_values_angles = xr.apply_ufunc(
        lambda x: (np.angle(x, deg=True) + 360) % 360, iq_values_translated
    )

    def state_filter(angles_array: xr.DataArray) -> xr.DataArray:
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

    assigned_states = xr.apply_ufunc(state_filter, iq_values_angles)
    return assigned_states
