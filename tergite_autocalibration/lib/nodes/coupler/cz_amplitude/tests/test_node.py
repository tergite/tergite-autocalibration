import numpy as np
import pytest
from tergite_autocalibration.lib.nodes.coupler.cz_amplitude.node import CZ_Amplitude_Node
from tergite_autocalibration.lib.utils.node_subclasses import ParametrizedSweepNode

def test_canCreateCorrectType():
    c = CZ_Amplitude_Node("cz_ampl", couplers = ["q14_q15"])
    assert isinstance(c, CZ_Amplitude_Node)
    assert isinstance(c, ParametrizedSweepNode)

def test_CanGetQubitsFromCouplers():
    c = CZ_Amplitude_Node("cz_ampl", couplers = ["q14_q15"])
    assert c.all_qubits == ["q14", "q15"]
    assert c.couplers == ['q14_q15']

def test_ValidationReturnErrorWithSameQubitCoupler():
    with pytest.raises(ValueError):
        c = CZ_Amplitude_Node("cz_ampl", couplers = ["q14_q14"])
 