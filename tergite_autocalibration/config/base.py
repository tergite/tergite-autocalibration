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

from abc import ABC
from pathlib import Path
from typing import Union

import toml


class BaseConfigurationFile(ABC):

    def __init__(self, filepath: Union[str, Path]):
        self._filepath = None
        self.filepath = filepath

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, value):
        self._filepath = value


class TOMLConfigurationFile(BaseConfigurationFile):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dict = toml.load(self.filepath)
