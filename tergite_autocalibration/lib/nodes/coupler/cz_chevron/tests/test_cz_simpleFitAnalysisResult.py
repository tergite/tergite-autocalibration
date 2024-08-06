from tergite_autocalibration.tests.utils.env import setup_test_env

setup_test_env()

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
