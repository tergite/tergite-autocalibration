# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from ..utils.cz_FitResultStatus import (
    FitResultStatus,
)
from ..utils.cz_simpleFitAnalysisResult import (
    CZSimpleFitAnalysisResult,
)


def test_canCreate():
    r = CZSimpleFitAnalysisResult()
    assert r.status == FitResultStatus.NOT_AVAILABLE


def test_canInitialise():
    pv1 = 0.99
    pv2 = 0.995
    param_1 = [0.4, 100, 30, 0.6]
    param_2 = [0.6, 120, 110, 0.6]
    status = FitResultStatus.FOUND
    r = CZSimpleFitAnalysisResult(pv1, pv2, param_1, param_2, status)
    assert r.status == FitResultStatus.FOUND
    assert r.pvalue_1 == pv1
    assert r.pvalue_2 == pv2
    assert r.fittedParam_1 == param_1
    assert r.fittedParam_2 == param_2
