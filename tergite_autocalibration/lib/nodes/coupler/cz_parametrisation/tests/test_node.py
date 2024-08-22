import numpy as np
import pytest
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.analysis import (
    CZParametrisationFixDurationAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.measurement import (
    CZParametrisationFixDuration,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.node import (
    CZParametrisationFixDurationNode,
)
from tergite_autocalibration.lib.utils.node_subclasses import ParametrizedSweepNode


def test_canCreateCorrectType():
    c = CZParametrisationFixDurationNode("cz_char_fixCurrent", all_qubits = ["q14", "q15"], couplers=["q14_q15"])
    assert isinstance(c, CZParametrisationFixDurationNode)
    assert isinstance(c, ParametrizedSweepNode)


def test_CanGetQubitsFromCouplers():
    c = CZParametrisationFixDurationNode("cz_char_fixCurrent", all_qubits = ["q14", "q15"], couplers=["q14_q15"])
    assert c.all_qubits == ["q14", "q15"]
    assert c.couplers == ["q14_q15"]


def test_ValidationReturnErrorWithSameQubitCoupler():
    with pytest.raises(ValueError):
        CZParametrisationFixDurationNode("cz_char_fixCurrent", all_qubits = ["q14", "q15"], couplers=["q14_q14"])

def test_ValidationReturnErrorWithQubitsNotMatchingClouples():
    with pytest.raises(ValueError):
        CZParametrisationFixDurationNode("cz_char_fixCurrent", all_qubits = ["q14", "q16"], couplers=["q14_q15"])


def test_MeasurementClassType():
    c = CZParametrisationFixDurationNode("cz_char_fixCurrent", all_qubits = ["q14", "q15"], couplers=["q14_q15"])
    assert isinstance(c.measurement_obj, type(CZParametrisationFixDuration))


def test_AnalysisClassType():
    c = CZParametrisationFixDurationNode("cz_char_fixCurrent", all_qubits = ["q14", "q15"], couplers=["q14_q15"])
    assert isinstance(c.analysis_obj, type(CZParametrisationFixDurationAnalysis))
