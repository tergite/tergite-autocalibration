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


class CZSingleGateSimpleFitResult:
    def __init__(self, p=None, f=None, s=FitResultStatus.NOT_AVAILABLE) -> None:
        self.pvalues = p
        self.fittedParams = f
        self.status = s
