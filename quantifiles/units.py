import numpy as np

known_units = {
    "mA": 1e-3,
    "uA": 1e-6,
    "nA": 1e-9,
    "pA": 1e-12,
    "fA": 1e-15,
    "nV": 1e-9,
    "uV": 1e-6,
    "mV": 1e-3,
    "kV": 1e3,
    "MV": 1e6,
    "GV": 1e9,
    "nT": 1e-9,
    "uT": 1e-6,
    "mT": 1e-3,
    "kT": 1e3,
    "MT": 1e6,
    "GT": 1e9,
    "nH": 1e-9,
    "uH": 1e-6,
    "mH": 1e-3,
    "kH": 1e3,
    "MH": 1e6,
    "GH": 1e9,
    "ns": 1e-9,
    "us": 1e-6,
    "ms": 1e-3,
    "kHz": 1e3,
    "MHz": 1e6,
    "GHz": 1e9,
}


def get_si_unit_and_scaling(unit: str) -> (str, float):
    scaler = 1
    if unit in known_units.keys():
        scaler = known_units[unit]
        unit = unit[1:]

    return unit, scaler


def format_value_and_unit(value: float, unit: str) -> str:
    unit, scaler = get_si_unit_and_scaling(unit)
    if np.isnan(value):
        value = 0
    return f"{value * scaler: .4e}" + unit


def get_si_unit(unit: str) -> str:
    return get_si_unit_and_scaling(unit)[0]


def get_unit_scaling(unit) -> float:
    return get_si_unit_and_scaling(unit)[1]


if __name__ == "__main__":
    s = format_value_and_unit(50, "mV")
    print(s)
