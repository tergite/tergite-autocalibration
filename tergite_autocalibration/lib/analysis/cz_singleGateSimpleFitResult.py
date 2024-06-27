from tergite_acl.lib.analysis.cz_FitResultStatus import FitResultStatus

class CZSingleGateSimpleFitResult():
    def __init__(self, p=None , f=None, s=FitResultStatus.NOT_AVAILABLE) -> None:
        self.pvalues = p
        self.fittedParams = f
        self.status = s