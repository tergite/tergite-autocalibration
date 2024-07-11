import pytest

from tergite_autocalibration.lib.nodes.coupler.cz_amplitude.node import CZ_Amplitude_Node
from tergite_autocalibration.lib.utils.node_subclasses import ParametrizedSweepNode


def test_canCreate():
    c = CZ_Amplitude_Node("cz_ampl","[q1, q2]")
    assert isinstance(c, CZ_Amplitude_Node)
    assert isinstance(c, ParametrizedSweepNode)
    
