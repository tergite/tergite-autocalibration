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

import os
import typing
import warnings
from pathlib import Path

from dotenv import dotenv_values

T = typing.TypeVar("T")


def from_environment(key_name_: str, cast_: type = str, default: T = None) -> T:
    """
    Helper function to read keys from the .env file

    Args:
        key_name_: Name of the variable to read from .env
        cast_: Cast variable to type T
        default: Default value for the variable (will be checked for type T)

    Returns:
        Type-checked-and-casted variable from .env

    """

    if os.environ.get(key_name_) is not None:
        try:
            if cast_ is bool:
                return eval(os.environ.get(key_name_))
            return cast_(os.environ.get(key_name_))
        except ValueError:
            raise ValueError(
                f"Variable with name {key_name_} from system environmental variables with value "
                f"{os.environ.get(key_name_)} cannot be casted to type {cast_}"
            )
    elif key_name_ in config:
        try:
            if cast_ is bool:
                return eval(config[key_name_])
            return cast_(config[key_name_])
        except ValueError:
            raise ValueError(
                f"Variable with name {key_name_} from .env with value {config[key_name_]} "
                f"cannot be casted to type {cast_}"
            )
    elif default is not None:
        # This is mainly a check for ourselves
        assert isinstance(default, cast_)
        return default
    else:
        warnings.warn(f"Cannot read {key_name_} from environment variables.")
        return None


config = dotenv_values(Path(__file__).parent.parent.parent.joinpath(".env"))
