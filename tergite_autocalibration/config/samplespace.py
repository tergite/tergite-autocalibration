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

import importlib.util
import sys
from typing import Any, Dict

from tergite_autocalibration.config.base import BaseConfigurationFile


class SamplespaceConfiguration(BaseConfigurationFile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically load the module from the user_samplespace.py file
        # If you are experiencing circular imports, please check that you are not importing
        # anything from tergite_autocalibration inside the user_samplespace.py file.
        # If you are experiencing any errors that the module cannot be loaded, please make
        # sure that the user_samplespace.py file from your configuration contains a variable
        # with the name "user_samplespace".
        if self.filepath is not None:
            us_spec_ = importlib.util.spec_from_file_location(
                "user_samplespace", self.filepath
            )
            samplespace_ = importlib.util.module_from_spec(us_spec_)
            sys.modules["user_samplespace"] = samplespace_
            us_spec_.loader.exec_module(samplespace_)
            self._samplespace = samplespace_.user_samplespace
        else:
            self._samplespace = {}

    def __call__(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Returns:
            This is just for convenience.
            In case there is an instance of `SamplespaceConfiguration`, you can just call it
            >>> samplespace = SamplespaceConfiguration('path/to/user_samplespace.py')
            >>> user_samplespace: dict = samplespace()
            Alternatively, the `SamplespaceConfiguration` could inherit from dict as suggested in:
            https://gitlab.quantum.chalmersnextlabs.se/chalmersnextlabs-quantum/autocalibration/tergite-autocalibration/-/issues/42

        """
        return self._samplespace
