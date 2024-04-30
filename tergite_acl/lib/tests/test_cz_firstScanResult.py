import pytest
import xarray as xr
import numpy as np
from tergite_acl.lib.analysis.cz_firstScanResult import CZFirstScanResult,FitResultStatus

def test_canCreate():
    r = CZFirstScanResult()
    assert r.status == FitResultStatus.NOT_AVAILABLE

def test_canInitialise():
    fittedParams = [0, 1, 2]
    status = FitResultStatus.FOUND
    pvalues = [0.1, 0.2, 0.9]
    r = CZFirstScanResult(pvalues, fittedParams, status)
    assert r.status == FitResultStatus.FOUND
    assert r.fittedParams == [0, 1, 2]
    assert r.pvalues == [0.1, 0.2, 0.9]
