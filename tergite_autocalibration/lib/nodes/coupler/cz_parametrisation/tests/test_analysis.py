from tergite_autocalibration.lib.base.analysis import BaseAnalysis
from tergite_autocalibration.lib.nodes.coupler.cz_characterisation.analysis import CZ_Parametrisation_Fix_Duration_Analysis


def test_CanCreate():
    a = CZ_Parametrisation_Fix_Duration_Analysis()
    assert isinstance(a, CZ_Parametrisation_Fix_Duration_Analysis)
    assert isinstance(a, BaseAnalysis)