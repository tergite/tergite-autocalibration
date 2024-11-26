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

from tergite_autocalibration.config.base import BaseConfigurationFile


class SamplespaceConfiguration(BaseConfigurationFile):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    def __call__(self, *args, **kwargs):
        return self._samplespace
