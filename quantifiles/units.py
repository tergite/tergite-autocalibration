from __future__ import annotations

import numpy as np

known_units = {
    "A": 1,
    "mA": 1e-3,
    "uA": 1e-6,
    "nA": 1e-9,
    "pA": 1e-12,
    "fA": 1e-15,
    "nV": 1e-9,
    "uV": 1e-6,
    "mV": 1e-3,
    "V": 1,
    "kV": 1e3,
    "MV": 1e6,
    "GV": 1e9,
    "nT": 1e-9,
    "uT": 1e-6,
    "mT": 1e-3,
    "T": 1,
    "kT": 1e3,
    "MT": 1e6,
    "GT": 1e9,
    "nH": 1e-9,
    "uH": 1e-6,
    "mH": 1e-3,
    "H": 1,
    "kH": 1e3,
    "MH": 1e6,
    "GH": 1e9,
    "ns": 1e-9,
    "us": 1e-6,
    "ms": 1e-3,
    "s": 1,
    "Hz": 1,
    "kHz": 1e3,
    "MHz": 1e6,
    "GHz": 1e9,
}


def get_si_unit_and_scaling(unit: str) -> (str | None, float):
    """
    Given a string unit, return its SI unit and scaling factor.

    Args:
        unit: The unit to convert.

    Returns:
        A tuple containing the SI unit and scaling factor.
    """
    if unit in known_units.keys():
        scaling = known_units[unit]
        si_unit = unit if scaling == 1 else unit[1:]
        return si_unit, scaling
    else:
        return None, 1.0


def format_value_and_unit(value: float, unit: str) -> str:
    unit, scaler = get_si_unit_and_scaling(unit)
    if np.isnan(value):
        value = 0
    return f"{value * scaler:.4e}" + unit
