import numpy as np
import pytest
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.analysis import (
    CZParametrisationFixDurationAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.measurement import (
    CZParametrisationFixDuration,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.node import (
    CZ_Parametrisation_Fix_Duration_Node,
)
from tergite_autocalibration.lib.utils.node_subclasses import ParametrizedSweepNode


def test_canCreateCorrectType():
    c = CZ_Parametrisation_Fix_Duration_Node("cz_char_fixCurrent", couplers=["q14_q15"])
    assert isinstance(c, CZ_Parametrisation_Fix_Duration_Node)
    assert isinstance(c, ParametrizedSweepNode)


def test_CanGetQubitsFromCouplers():
    c = CZ_Parametrisation_Fix_Duration_Node("cz_char_fixCurrent", couplers=["q14_q15"])
    assert c.all_qubits == ["q14", "q15"]
    assert c.couplers == ["q14_q15"]


def test_ValidationReturnErrorWithSameQubitCoupler():
    with pytest.raises(ValueError):
        CZ_Parametrisation_Fix_Duration_Node("cz_char_fixCurrent", couplers=["q14_q14"])


def test_MeasurementClassType():
    c = CZ_Parametrisation_Fix_Duration_Node("cz_char_fixCurrent", couplers=["q14_q15"])
    assert isinstance(c.measurement_obj, type(CZParametrisationFixDuration))


def test_AnalysisClassType():
    c = CZ_Parametrisation_Fix_Duration_Node("cz_char_fixCurrent", couplers=["q14_q15"])
    assert isinstance(c.analysis_obj, type(CZParametrisationFixDurationAnalysis))
