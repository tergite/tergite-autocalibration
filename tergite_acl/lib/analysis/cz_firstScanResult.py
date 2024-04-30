from enum import Enum
class FitResultStatus(Enum):
    NOT_AVAILABLE = 0
    NOT_FOUND = 1
    FOUND = 2
    
class CZFirstScanResult():
    def __init__(self, p=None , f=None, s=FitResultStatus.NOT_AVAILABLE) -> None:
        self.pvalues = p
        self.fittedParams = f
        self.status = s