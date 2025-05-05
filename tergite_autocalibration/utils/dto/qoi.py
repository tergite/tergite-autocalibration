# This code is part of Tergite
#
# (C) Copyright Stefan Hill 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


class QOI:
    def __init__(self, analysis_result: dict, analysis_successful: bool):
        """
        Initialize the QOI
        TODO: This is for now just a mock class, which we use for the type checking
        """
        self.analysis_successful = analysis_successful
        self.analysis_result = analysis_result
