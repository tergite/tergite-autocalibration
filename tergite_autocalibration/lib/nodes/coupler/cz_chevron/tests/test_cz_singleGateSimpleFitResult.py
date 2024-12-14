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

from ..utils.cz_singleGateSimpleFitResult import (
    CZSingleGateSimpleFitResult,
    FitResultStatus,
)


def test_canCreate():
    r = CZSingleGateSimpleFitResult()
    assert r.status == FitResultStatus.NOT_AVAILABLE


def test_canInitialise():
    fittedParams = [[0, 1, 2, 4], [0, 1, 2, 4], [0, 1, 2, 4]]
    status = FitResultStatus.FOUND
    pvalues = [0.1, 0.2, 0.9]
    r = CZSingleGateSimpleFitResult(pvalues, fittedParams, status)
    assert r.status == FitResultStatus.FOUND
    assert r.fittedParams == [[0, 1, 2, 4], [0, 1, 2, 4], [0, 1, 2, 4]]
    assert r.pvalues == [0.1, 0.2, 0.9]
