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

from functools import wraps
from typing import Dict, Any


GLOBAL_VARIABLES = {"ABC": 123, "CDE": 345}


def set_test_env(variables: Dict[str, Any]):
    def inner_decorator_fn_(fn_):
        @wraps(fn_)
        def wrapper(*args, **kwargs):
            # Temporarily store all variables in a cache
            temp_variable_storage_ = {}
            for variable_name, variable_value in variables.items():
                # TODO: This now has to be injected into the module instead
                temp_variable_storage_[variable_name] = GLOBAL_VARIABLES[variable_name]
                GLOBAL_VARIABLES[variable_name] = variable_value

            result = fn_(*args, **kwargs)

            # Reset all variables
            for variable_name, variable_value in temp_variable_storage_.items():
                GLOBAL_VARIABLES[variable_name] = temp_variable_storage_[variable_name]

            # Return the result of the function
            return result

        return wrapper

    return inner_decorator_fn_


@set_test_env({"ABC": 345})
def test_setting_env_variables():
    print(GLOBAL_VARIABLES)
