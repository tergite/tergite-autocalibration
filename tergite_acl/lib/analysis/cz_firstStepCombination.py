from typing import Type
import numpy as np
from tergite_acl.lib.analysis.cz_FitResultStatus import FitResultStatus
from tergite_acl.lib.analysis.cz_simpleFitAnalysisResult import CZSimpleFitAnalysisResult
from tergite_acl.lib.analysis.cz_singleGateSimpleFitResult import CZSingleGateSimpleFitResult

class CZFirstStepCombination():
    def __init__(self, r1: Type[CZSingleGateSimpleFitResult], r2: Type[CZSingleGateSimpleFitResult]):
        self.result1: Type[CZSingleGateSimpleFitResult] = r1
        self.result2: Type[CZSingleGateSimpleFitResult] = r2

    def Analyze(self) -> CZSimpleFitAnalysisResult:
        highest_pv_1 = np.max(self.result1.pvalues)
        highest_pv_2 = np.max(self.result2.pvalues)

        indeces_max_pv1 = np.where(self.result1.pvalues == highest_pv_1)
        indeces_max_pv2 = np.where(self.result2.pvalues == highest_pv_2)

        indeces_max_pv = np.intersect1d(indeces_max_pv1, indeces_max_pv2)

        r = CZSimpleFitAnalysisResult()
        
        if indeces_max_pv.size > 0:
            indexMax = indeces_max_pv[0] #pick the first
            r.fittedParam_1 = self.result1.fittedParams[indexMax]
            r.fittedParam_2 = self.result2.fittedParams[indexMax]
            r.pvalue_1 = self.result1.pvalues[indexMax]
            r.pvalue_2 = self.result2.pvalues[indexMax]
            r.indexBestFrequency = indexMax
            r.status = FitResultStatus.FOUND
        else:
            r.status = FitResultStatus.NOT_FOUND

        return r
