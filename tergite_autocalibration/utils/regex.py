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

import re


def camel_to_snake(camel_str):
    # Handle uppercase letters followed by a lowercase letter
    snake_str = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", camel_str)
    snake_str = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", snake_str)
    # Insert underscores before digits
    snake_str = re.sub(r"(\D)(\d)", r"\1_\2", snake_str)
    return snake_str.lower()
