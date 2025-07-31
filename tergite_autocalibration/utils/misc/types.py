# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from typing import Union, Type


def safe_str_to_bool_int_float(
    expected_type: Union[
        bool, int, float, str, Type[bool], Type[int], Type[float], Type[str]
    ],
    value: str,
) -> Union[bool, int, float, str]:
    """
    Converts a string to the given type

    Args:
        expected_type: The type T to cast the value to, can be bool, float, int or str
        value: The value to be cast

    Returns:

    """

    # Convert boolean strings to actual booleans
    if expected_type is bool:
        typed_value = str_to_bool(value) if is_bool(value) else False

    # Convert to integer
    elif expected_type is int:
        try:
            typed_value = int(value)
        except ValueError:
            raise ValueError(f"Cannot convert '{value}' to int: {value}")

    # Convert to float
    elif expected_type is float:
        try:
            typed_value = float(value)
        except ValueError:
            raise ValueError(f"Cannot convert '{value}' to float: {value}")
    else:
        typed_value = value
    return typed_value


def is_bool(s: str) -> bool:
    """
    Checks whether a given string could be parsed to bool

    Args:
        s: String to be parsed

    Returns:

    """
    return s.lower() in {"true", "false"}


def str_to_bool(s: str) -> bool:
    """
    Casts a string to bool, can be either upper or lower case

    Args:
        s: String to cast

    Returns:

    """
    if s.lower() == "true":
        return True
    elif s.lower() == "false":
        return False
    else:
        raise TypeError(f"String {s} cannot be casted to bool.")


def is_none_str(str_: str) -> bool:
    """
    Check whether a given string is None.

    Args:
        str_: String to check

    Returns:
        True if the string is "None" or "none".

    """
    return str_.strip().lower() == "none"
