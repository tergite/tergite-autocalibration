from tergite_acl.lib.analysis.cz_FitResultStatus import FitResultStatus
    
class CZSimpleFitAnalysisResult():
    def __init__(self, pv1=None , pv2=None, par1=None , par2=None, s=FitResultStatus.NOT_AVAILABLE) -> None:
        self.pvalue_1 = pv1
        self.fittedParam_1 = par1
        self.pvalue_2 = pv2
        self.fittedParam_2 = par2
        self.indexBestFrequency = None
        self.status = s

    def Print(self):
        print(f'Best freq idx: {self.indexBestFrequency}')       
        print(f'p-value_1: {self.pvalue_1}')
        print(f'p-value_2: {self.pvalue_2}')
        print(f'par1: {self.fittedParam_1}')
        print(f'par2: {self.fittedParam_2}')        
        print(f'')        