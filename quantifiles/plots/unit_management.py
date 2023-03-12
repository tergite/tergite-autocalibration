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
    "ns": 1e-9,
    "us": 1e-6,
    "ms": 1e-3,
    "kHz": 1e3,
    "MHz": 1e6,
    "GHz": 1e9,
}


def fix_units(unit):
    scaler = 1
    if unit in known_units.keys():
        scaler = known_units[unit]
        unit = unit[1:]

    return unit, scaler


def format_value_and_unit(value, unit, precision=1):
    unit, scaler = fix_units(unit)
    if np.isnan(value):
        value = 0
    return str(value * scaler) + unit  # removed si_format


def format_unit(unit):
    return fix_units(unit)[0]


def return_unit_scaler(unit):
    return fix_units(unit)[1]


if __name__ == "__main__":
    s = format_value_and_unit(50, "mV", precision=3)
    print(s)
