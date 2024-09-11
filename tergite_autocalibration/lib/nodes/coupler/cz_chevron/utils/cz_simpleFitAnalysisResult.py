# This code is part of Tergite
#
# (C) Copyright Michele Faucci Gianelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from tergite_autocalibration.lib.nodes.coupler.cz_chevron.utils.cz_FitResultStatus import (
    FitResultStatus,
)


class CZSimpleFitAnalysisResult:
    def __init__(
        self, pv1=None, pv2=None, par1=None, par2=None, s=FitResultStatus.NOT_AVAILABLE
    ) -> None:
        self.pvalue_1 = pv1
        self.fittedParam_1 = par1
        self.pvalue_2 = pv2
        self.fittedParam_2 = par2
        self.indexBestFrequency = None
        self.status = s

    def Print(self):
        print(f"Best freq idx: {self.indexBestFrequency}")
        print(f"p-value_1: {self.pvalue_1}")
        print(f"p-value_2: {self.pvalue_2}")
        print(f"par1: {self.fittedParam_1}")
        print(f"par2: {self.fittedParam_2}")
        print(f"")
