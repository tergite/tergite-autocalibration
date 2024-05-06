from typing import Type
import numpy as np
from tergite_acl.lib.analysis.cz_FitResultStatus import FitResultStatus
from tergite_acl.lib.analysis.cz_simpleFitAnalysisResult import CZSimpleFitAnalysisResult
from tergite_acl.lib.analysis.cz_singleGateSimpleFitResult import CZSingleGateSimpleFitResult

class CZFirstStepCombination():
    def __init__(self, r1: Type[CZSingleGateSimpleFitResult], r2: Type[CZSingleGateSimpleFitResult], freq):
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

        if self.result1.status == FitResultStatus.NOT_AVAILABLE or self.result1.status == FitResultStatus.NOT_FOUND or self.result2.status == FitResultStatus.NOT_AVAILABLE or self.result2.status == FitResultStatus.NOT_FOUND:
            r.status = FitResultStatus.NOT_FOUND
            return r
        
        # same index, easy
        if indices_max_pv.size > 0:
            indexMax = indices_max_pv[0] #pick the first
            r.fittedParam_1 = self.result1.fittedParams[indexMax]
            r.fittedParam_2 = self.result2.fittedParams[indexMax]
            r.pvalue_1 = self.result1.pvalues[indexMax]
            r.pvalue_2 = self.result2.pvalues[indexMax]
            r.indexBestFrequency = indexMax
            r.status = FitResultStatus.FOUND
        else:
            #close by index, need to pick the best
            indexMax1 = -1
            indexMax2 = -1
            currentBestPV = 0
            for idx1 in indices_max_pv1:
                for idx2 in indices_max_pv2:
                    if abs(idx1 - idx2) < 2:
                        if self.result1.pvalues[idx1] + self.result2.pvalues[idx2] > currentBestPV:
                            indexMax1 = idx1
                            indexMax2 = idx2
                            currentBestPV = self.result1.pvalues[idx1] + self.result2.pvalues[idx2]

            if indexMax1 != -1:
                r.fittedParam_1 = self.result1.fittedParams[indexMax1]
                r.fittedParam_2 = self.result2.fittedParams[indexMax2]
                r.pvalue_1 = self.result1.pvalues[indexMax1]
                r.pvalue_2 = self.result2.pvalues[indexMax2]
                r.indexBestFrequency = indexMax1
                r.status = FitResultStatus.FOUND
            
            else:
                #close by frequency, need to pick the best
                indexMax1 = -1
                indexMax2 = -1
                currentBestPV = 0
                for idx1 in indices_max_pv1:
                    for idx2 in indices_max_pv2:
                        if abs(self.freq[idx1] - self.freq[idx2]) < 3:
                            if self.result1.pvalues[idx1] + self.result2.pvalues[idx2] > currentBestPV:
                                indexMax1 = idx1
                                indexMax2 = idx2
                                currentBestPV = self.result1.pvalues[idx1] + self.result2.pvalues[idx2]

                if indexMax1 != -1:
                    r.fittedParam_1 = self.result1.fittedParams[indexMax1]
                    r.fittedParam_2 = self.result2.fittedParams[indexMax2]
                    r.pvalue_1 = self.result1.pvalues[indexMax1]
                    r.pvalue_2 = self.result2.pvalues[indexMax2]
                    r.indexBestFrequency = round((indexMax1 + indexMax2) / 2)
                    r.status = FitResultStatus.FOUND

                else:
                    r.status = FitResultStatus.NOT_FOUND

        return r
