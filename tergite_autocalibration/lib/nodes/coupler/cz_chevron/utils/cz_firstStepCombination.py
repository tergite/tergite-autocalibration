from typing import Type
import numpy as np
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.utils.cz_FitResultStatus import (
    FitResultStatus,
)
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.utils.cz_simpleFitAnalysisResult import (
    CZSimpleFitAnalysisResult,
)
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.utils.cz_singleGateSimpleFitResult import (
    CZSingleGateSimpleFitResult,
)


class CZFirstStepCombination:
    def __init__(
        self,
        r1: Type[CZSingleGateSimpleFitResult],
        r2: Type[CZSingleGateSimpleFitResult],
        freq,
    ):
        self.result1: Type[CZSingleGateSimpleFitResult] = r1
        self.result2: Type[CZSingleGateSimpleFitResult] = r2
        self.freq = freq

    def Analyze(self) -> CZSimpleFitAnalysisResult:
        highest_pv_1 = np.max(self.result1.pvalues)
        highest_pv_2 = np.max(self.result2.pvalues)

        indices_max_pv1 = np.where(self.result1.pvalues == highest_pv_1)[0]
        indices_max_pv2 = np.where(self.result2.pvalues == highest_pv_2)[0]

        indices_max_pv = np.intersect1d(indices_max_pv1, indices_max_pv2)

        r = CZSimpleFitAnalysisResult()

        if self.NotFoundOrAvailable(self.result1, self.result2):
            r.status = FitResultStatus.NOT_FOUND
            return r

        # same index, easy
        if indices_max_pv.size > 0:
            r = self.SameIndexResult(indices_max_pv)
        else:
            # close by index, need to pick the best
            r = self.NeightbourIndexResult(indices_max_pv1, indices_max_pv2)

            if r.status == FitResultStatus.NOT_AVAILABLE:
                # close by frequency, need to pick the best
                r = self.CloseByFrequencyResult(indices_max_pv1, indices_max_pv2)

                if r.status == FitResultStatus.NOT_AVAILABLE:
                    r.status = FitResultStatus.NOT_FOUND

        return r

    def NotFoundOrAvailable(self, r1, r2):
        return (
            r1.status == FitResultStatus.NOT_AVAILABLE
            or r1.status == FitResultStatus.NOT_FOUND
            or r2.status == FitResultStatus.NOT_AVAILABLE
            or r2.status == FitResultStatus.NOT_FOUND
        )

    def SameIndexResult(
        self, indices_max_pv: Type[np.ndarray]
    ) -> CZSimpleFitAnalysisResult:
        r = CZSimpleFitAnalysisResult()
        indexMax = indices_max_pv[0]  # pick the first
        r.fittedParam_1 = self.result1.fittedParams[indexMax]
        r.fittedParam_2 = self.result2.fittedParams[indexMax]
        r.pvalue_1 = self.result1.pvalues[indexMax]
        r.pvalue_2 = self.result2.pvalues[indexMax]
        r.indexBestFrequency = indexMax
        r.status = FitResultStatus.FOUND
        return r

    def NeightbourIndexResult(
        self, indices_max_pv1: Type[np.ndarray], indices_max_pv2: Type[np.ndarray]
    ) -> CZSimpleFitAnalysisResult:
        r = CZSimpleFitAnalysisResult()
        indexMax1, indexMax2 = self.GetIndicesThatHaveNeighbourBestPvalues(
            indices_max_pv1, indices_max_pv2
        )

        if indexMax1 != -1:
            r.fittedParam_1 = self.result1.fittedParams[indexMax1]
            r.fittedParam_2 = self.result2.fittedParams[indexMax2]
            r.pvalue_1 = self.result1.pvalues[indexMax1]
            r.pvalue_2 = self.result2.pvalues[indexMax2]
            r.indexBestFrequency = indexMax1
            r.status = FitResultStatus.FOUND

        return r

    def GetIndicesThatHaveNeighbourBestPvalues(self, indices_max_pv1, indices_max_pv2):
        indexMax1 = -1
        indexMax2 = -1
        currentBestPV = 0
        for idx1 in indices_max_pv1:
            for idx2 in indices_max_pv2:
                if abs(idx1 - idx2) < 2:
                    if (
                        self.result1.pvalues[idx1] + self.result2.pvalues[idx2]
                        > currentBestPV
                    ):
                        indexMax1 = idx1
                        indexMax2 = idx2
                        currentBestPV = (
                            self.result1.pvalues[idx1] + self.result2.pvalues[idx2]
                        )
        return indexMax1, indexMax2

    def CloseByFrequencyResult(
        self, indices_max_pv1: Type[np.ndarray], indices_max_pv2: Type[np.ndarray]
    ) -> CZSimpleFitAnalysisResult:
        r = CZSimpleFitAnalysisResult()
        indexMax1, indexMax2 = self.IndicesThatHaveCloseByFrequencies(
            indices_max_pv1, indices_max_pv2
        )

        if indexMax1 != -1:
            r.fittedParam_1 = self.result1.fittedParams[indexMax1]
            r.fittedParam_2 = self.result2.fittedParams[indexMax2]
            r.pvalue_1 = self.result1.pvalues[indexMax1]
            r.pvalue_2 = self.result2.pvalues[indexMax2]
            r.indexBestFrequency = round((indexMax1 + indexMax2) / 2)
            r.status = FitResultStatus.FOUND

        return r

    def IndicesThatHaveCloseByFrequencies(self, indices_max_pv1, indices_max_pv2):
        indexMax1 = -1
        indexMax2 = -1
        currentBestPV = 0
        for idx1 in indices_max_pv1:
            for idx2 in indices_max_pv2:
                if abs(self.freq[idx1] - self.freq[idx2]) < 3:
                    if (
                        self.result1.pvalues[idx1] + self.result2.pvalues[idx2]
                        > currentBestPV
                    ):
                        indexMax1 = idx1
                        indexMax2 = idx2
                        currentBestPV = (
                            self.result1.pvalues[idx1] + self.result2.pvalues[idx2]
                        )
        return indexMax1, indexMax2
