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
from functools import wraps
from typing import Dict, Any


def with_os_env(variables: Dict[str, Any]):
    """
    This is a decorator to - during a test - change the environmental variable configuration.
    This is more safe than setting the variables in the code directly, because it will also
    try to restore the original configuration after the function has been called.

    Args:
        variables: A dictionary of the environmental variables to be set

    Returns:

    """

    def inner_decorator_fn_(fn_):
        @wraps(fn_)
        def wrapper(*args, **kwargs):
            # Temporarily store all variables in a cache
            temp_variable_storage_ = {}
            for variable_name, variable_value in variables.items():
                # Store the actual value or None in the temporary dict
                temp_variable_storage_[variable_name] = os.getenv(variable_name, None)
                os.environ[variable_name] = str(variable_value)

            # This is in a try finally block to ensure that environmental variables are restored even
            # if the function raises an exception.
            try:
                result = fn_(*args, **kwargs)

            finally:
                # Reset all variables
                for variable_name, variable_value in temp_variable_storage_.items():
                    # If the variable did not exist in the environmental variables, delete it
                    if variable_value is None:
                        del os.environ[variable_name]
                    # Otherwise set it to the previous value
                    else:
                        os.environ[variable_name] = temp_variable_storage_[
                            variable_name
                        ]

            # Return the result of the function
            return result

        return wrapper

    return inner_decorator_fn_
