import numpy as np

from quantifiles.units import get_si_unit_and_scaling, format_value_and_unit


def test_get_si_unit_and_scaling_known_unit():
    assert get_si_unit_and_scaling("uA") == ("A", 1e-6)


def test_get_si_unit_and_scaling_unknown_unit():
    assert get_si_unit_and_scaling("foo") == (None, 1.0)


def test_format_value_and_unit_known_unit():
    assert format_value_and_unit(1, "uA") == "1.0000e-06A"


def test_format_value_and_unit_unknown_unit():
    assert format_value_and_unit(1e-6, "foo") == "1.0000e-06"


def test_format_value_and_unit_nan():
    assert format_value_and_unit(np.nan, "uA") == "0.0000e+00A"
