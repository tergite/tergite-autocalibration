from tergite_autocalibration.tests.utils.env import setup_test_env

setup_test_env()

from tergite_autocalibration.lib.nodes.coupler.cz_chevron.utils.cz_FitResultStatus import (
    FitResultStatus,
)
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.utils.cz_singleGateSimpleFitResult import (
    CZSingleGateSimpleFitResult,
)
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.utils.cz_firstStepCombination import (
    CZFirstStepCombination,
)


def test_goodResultReturnCorrectFrequency():
    r1 = CZSingleGateSimpleFitResult(
        [0.2, 0.995, 0.7],
        [None, [0.4, 100, 50, 0.6], [0.2, 200, 12, 0]],
        FitResultStatus.FOUND,
    )
    r2 = CZSingleGateSimpleFitResult(
        [0.1, 0.991, 0.8],
        [None, [0.32, 114, 110, 0.55], [0.6, 300, 12, 0]],
        FitResultStatus.FOUND,
    )
    freq = [10, 20, 30]
    comb = CZFirstStepCombination(r1, r2, freq)
    r = comb.Analyze()
    assert r.indexBestFrequency == 1
    assert r.fittedParam_1 == [0.4, 100, 50, 0.6]
    assert r.fittedParam_2 == [0.32, 114, 110, 0.55]
    assert r.pvalue_1 == 0.995
    assert r.pvalue_2 == 0.991
    assert r.status == FitResultStatus.FOUND


def test_poorResultReturnCorrectFrequency():
    r1 = CZSingleGateSimpleFitResult(
        [0.2, 0.8, 0.7],
        [None, [0.4, 100, 50, 0.6], [0.2, 200, 12, 0]],
        FitResultStatus.FOUND,
    )
    r2 = CZSingleGateSimpleFitResult(
        [0.1, 0.8, 0.6],
        [None, [0.32, 114, 110, 0.55], [0.6, 300, 12, 0]],
        FitResultStatus.FOUND,
    )
    freq = [10, 20, 30]
    comb = CZFirstStepCombination(r1, r2, freq)
    r = comb.Analyze()
    assert r.indexBestFrequency == 1
    assert r.fittedParam_1 == [0.4, 100, 50, 0.6]
    assert r.fittedParam_2 == [0.32, 114, 110, 0.55]
    assert r.pvalue_1 == 0.8
    assert r.pvalue_2 == 0.8
    assert r.status == FitResultStatus.FOUND


def test_samePvalueReturnCorrectFrequency():
    r1 = CZSingleGateSimpleFitResult(
        [0.2, 0.8, 0.7],
        [None, [0.4, 100, 50, 0.6], [0.2, 200, 12, 0]],
        FitResultStatus.FOUND,
    )
    r2 = CZSingleGateSimpleFitResult(
        [0.1, 0.8, 0.8],
        [None, [0.32, 114, 110, 0.55], [0.6, 300, 12, 0]],
        FitResultStatus.FOUND,
    )
    freq = [10, 20, 30]
    comb = CZFirstStepCombination(r1, r2, freq)
    r = comb.Analyze()
    assert r.indexBestFrequency == 1
    assert r.fittedParam_1 == [0.4, 100, 50, 0.6]
    assert r.fittedParam_2 == [0.32, 114, 110, 0.55]
    assert r.pvalue_1 == 0.8
    assert r.pvalue_2 == 0.8
    assert r.status == FitResultStatus.FOUND


def test_samePvalueNotFirstPositionReturnCorrectFrequency():
    r1 = CZSingleGateSimpleFitResult(
        [0.2, 0.5, 0.7],
        [None, [0.4, 100, 50, 0.6], [0.2, 200, 12, 0]],
        FitResultStatus.FOUND,
    )
    r2 = CZSingleGateSimpleFitResult(
        [0.1, 0.8, 0.8],
        [None, [0.32, 114, 110, 0.55], [0.6, 300, 12, 0]],
        FitResultStatus.FOUND,
    )
    freq = [10, 20, 30]
    comb = CZFirstStepCombination(r1, r2, freq)
    r = comb.Analyze()
    assert r.indexBestFrequency == 2
    assert r.fittedParam_1 == [0.2, 200, 12, 0]
    assert r.fittedParam_2 == [0.6, 300, 12, 0]
    assert r.pvalue_1 == 0.7
    assert r.pvalue_2 == 0.8
    assert r.status == FitResultStatus.FOUND


def test_neighbourBestResultReturnFrequencyOfFirstQubitButValuesFromEachBest():
    r1 = CZSingleGateSimpleFitResult(
        [0.2, 0.8, 0.7],
        [None, [0.4, 100, 50, 0.6], [0.2, 200, 12, 0]],
        FitResultStatus.FOUND,
    )
    r2 = CZSingleGateSimpleFitResult(
        [0.1, 0.5, 0.8],
        [None, [0.32, 114, 110, 0.55], [0.6, 300, 12, 0]],
        FitResultStatus.FOUND,
    )
    freq = [10, 20, 30]
    comb = CZFirstStepCombination(r1, r2, freq)
    r = comb.Analyze()
    assert r.indexBestFrequency == 1
    assert r.fittedParam_1 == [0.4, 100, 50, 0.6]
    assert r.fittedParam_2 == [0.6, 300, 12, 0]
    assert r.pvalue_1 == 0.8
    assert r.pvalue_2 == 0.8
    assert r.status == FitResultStatus.FOUND


def test_neighbourBestResultReturnFrequencyOfFirstQubitButValuesFromEachBestInverted():
    r1 = CZSingleGateSimpleFitResult(
        [0.2, 0.6, 0.7],
        [None, [0.4, 100, 50, 0.6], [0.2, 200, 12, 0]],
        FitResultStatus.FOUND,
    )
    r2 = CZSingleGateSimpleFitResult(
        [0.1, 0.9, 0.8],
        [None, [0.32, 114, 110, 0.55], [0.6, 300, 12, 0]],
        FitResultStatus.FOUND,
    )
    freq = [10, 20, 30]
    comb = CZFirstStepCombination(r1, r2, freq)
    r = comb.Analyze()
    assert r.indexBestFrequency == 2
    assert r.fittedParam_1 == [0.2, 200, 12, 0]
    assert r.fittedParam_2 == [0.32, 114, 110, 0.55]
    assert r.pvalue_1 == 0.7
    assert r.pvalue_2 == 0.9
    assert r.status == FitResultStatus.FOUND


def test_BestDistantBy2IndicesReturnNotFound():
    r1 = CZSingleGateSimpleFitResult(
        [0.8, 0.6, 0.7],
        [None, [0.4, 100, 50, 0.6], [0.2, 200, 12, 0]],
        FitResultStatus.FOUND,
    )
    r2 = CZSingleGateSimpleFitResult(
        [0.1, 0.5, 0.8],
        [None, [0.32, 114, 110, 0.55], [0.6, 300, 12, 0]],
        FitResultStatus.FOUND,
    )
    freq = [10, 20, 30]
    comb = CZFirstStepCombination(r1, r2, freq)
    r = comb.Analyze()
    assert r.status == FitResultStatus.NOT_FOUND


def test_BestDistantBy2IndicesButWithintFrequencyReturnMedianFrequency():
    r1 = CZSingleGateSimpleFitResult(
        [0.8, 0.6, 0.7],
        [[0.3, 105, 150, 0.4], [0.4, 100, 50, 0.6], [0.2, 200, 12, 0]],
        FitResultStatus.FOUND,
    )
    r2 = CZSingleGateSimpleFitResult(
        [0.1, 0.5, 0.8],
        [None, [0.32, 114, 110, 0.55], [0.6, 300, 12, 0]],
        FitResultStatus.FOUND,
    )
    freq = [19, 20, 21]
    comb = CZFirstStepCombination(r1, r2, freq)
    r = comb.Analyze()
    assert r.indexBestFrequency == 1
    assert r.fittedParam_1 == [0.3, 105, 150, 0.4]
    assert r.fittedParam_2 == [0.6, 300, 12, 0]
    assert r.pvalue_1 == 0.8
    assert r.pvalue_2 == 0.8
    assert r.status == FitResultStatus.FOUND


def test_failedFit1ReturnNone():
    r1 = CZSingleGateSimpleFitResult(
        [0.2, 0.8, 0.7],
        [None, [0.4, 100, 50, 0.6], [0.2, 200, 12, 0]],
        FitResultStatus.NOT_FOUND,
    )
    r2 = CZSingleGateSimpleFitResult(
        [0.1, 0.5, 0.8],
        [None, [0.32, 114, 110, 0.55], [0.6, 300, 12, 0]],
        FitResultStatus.FOUND,
    )
    freq = [10, 20, 30]
    comb = CZFirstStepCombination(r1, r2, freq)
    r = comb.Analyze()
    assert r.status == FitResultStatus.NOT_FOUND


def test_failedFit2ReturnNone():
    r1 = CZSingleGateSimpleFitResult(
        [0.2, 0.8, 0.7],
        [None, [0.4, 100, 50, 0.6], [0.2, 200, 12, 0]],
        FitResultStatus.FOUND,
    )
    r2 = CZSingleGateSimpleFitResult(
        [0.1, 0.5, 0.8],
        [None, [0.32, 114, 110, 0.55], [0.6, 300, 12, 0]],
        FitResultStatus.NOT_FOUND,
    )
    freq = [10, 20, 30]
    comb = CZFirstStepCombination(r1, r2, freq)
    r = comb.Analyze()
    assert r.status == FitResultStatus.NOT_FOUND


def test_resultNotAvailable1ReturnNone():
    r1 = CZSingleGateSimpleFitResult(
        [0.2, 0.8, 0.7],
        [None, [0.4, 100, 50, 0.6], [0.2, 200, 12, 0]],
        FitResultStatus.NOT_AVAILABLE,
    )
    r2 = CZSingleGateSimpleFitResult(
        [0.1, 0.5, 0.8],
        [None, [0.32, 114, 110, 0.55], [0.6, 300, 12, 0]],
        FitResultStatus.FOUND,
    )
    freq = [10, 20, 30]
    comb = CZFirstStepCombination(r1, r2, freq)
    r = comb.Analyze()
    assert r.status == FitResultStatus.NOT_FOUND


def test_resultNotAvailable2ReturnNone():
    r1 = CZSingleGateSimpleFitResult(
        [0.2, 0.8, 0.7],
        [None, [0.4, 100, 50, 0.6], [0.2, 200, 12, 0]],
        FitResultStatus.FOUND,
    )
    r2 = CZSingleGateSimpleFitResult(
        [0.1, 0.5, 0.8],
        [None, [0.32, 114, 110, 0.55], [0.6, 300, 12, 0]],
        FitResultStatus.NOT_AVAILABLE,
    )
    freq = [10, 20, 30]
    comb = CZFirstStepCombination(r1, r2, freq)
    r = comb.Analyze()
    assert r.status == FitResultStatus.NOT_FOUND
