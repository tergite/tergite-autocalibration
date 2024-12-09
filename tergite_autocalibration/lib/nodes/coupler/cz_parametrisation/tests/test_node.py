# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import pytest

from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.analysis import (
    CZParametrizationFixDurationNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.measurement import (
    CZParametrizationFixDuration,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.node import (
    CZParametrizationFixDurationNode,
)


@pytest.mark.skip
def test_canCreateCorrectType():
    c = CZParametrizationFixDurationNode(
        "cz_char_fixCurrent",
        all_qubits=["q14", "q15"],
        couplers=["q14_q15"],
    )
    assert isinstance(c, CZParametrizationFixDurationNode)
    assert isinstance(c, ScheduleNode)


@pytest.mark.skip
def test_CanGetQubitsFromCouplers():
    c = CZParametrizationFixDurationNode(
        "cz_char_fixCurrent", all_qubits=["q14", "q15"], couplers=["q14_q15"]
    )
    assert c.all_qubits == ["q14", "q15"]
    assert c.couplers == ["q14_q15"]


@pytest.mark.skip
def test_ValidationReturnErrorWithSameQubitCoupler():
    with pytest.raises(ValueError):
        CZParametrizationFixDurationNode(
            "cz_char_fixCurrent", all_qubits=["q14", "q15"], couplers=["q14_q14"]
        )


@pytest.mark.skip
def test_ValidationReturnErrorWithQubitsNotMatchingClouples():
    with pytest.raises(ValueError):
        CZParametrizationFixDurationNode(
            "cz_char_fixCurrent", all_qubits=["q14", "q16"], couplers=["q14_q15"]
        )


@pytest.mark.skip
def test_MeasurementClassType():
    c = CZParametrizationFixDurationNode(
        "cz_char_fixCurrent", all_qubits=["q14", "q15"], couplers=["q14_q15"]
    )
    assert isinstance(c.measurement_obj, type(CZParametrizationFixDuration))


@pytest.mark.skip
def test_AnalysisClassType():
    c = CZParametrizationFixDurationNode(
        "cz_char_fixCurrent", all_qubits=["q14", "q15"], couplers=["q14_q15"]
    )
    assert isinstance(c.analysis_obj, type(CZParametrizationFixDurationNodeAnalysis))
