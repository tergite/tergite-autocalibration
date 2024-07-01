from tergite_autocalibration.tests.utils.env import setup_test_env

setup_test_env()

from tergite_autocalibration.lib.analysis.cz_singleGateSimpleFitResult import (
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
