from tergite_acl.lib.analysis.cz_FitResultStatus import FitResultStatus
    
class CZSimpleFitAnalysisResult():
    def __init__(self, pv1=None , pv2=None, par1=None , par2=None, s=FitResultStatus.NOT_AVAILABLE) -> None:
        self.pvalue_1 = pv1
        self.fittedParam_1 = par1
        self.pvalue_2 = pv2
        self.fittedParam_2 = par2
        self.indexBestFrequency = None
        self.status = s