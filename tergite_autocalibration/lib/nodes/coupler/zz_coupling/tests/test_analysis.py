# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou  2026
# (C) Chalmers Next Labs AB 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os
from pathlib import Path

import pytest

from tergite_autocalibration.lib.nodes.coupler.cz_local_phases.analysis import (
    CZLocalPhasesCouplerAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.zz_coupling.analysis import (
    ZZCouplingCouplerAnalysis,
)
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.utils.io.dataset import open_dataset

_test_data_dir = Path(os.path.join(Path(__file__).parent, "data"))
_redis_values = os.path.join(_test_data_dir, "redis-2026-05-27.json")


@with_redis(_redis_values)
def test_zz_coupling():
    name = "zz_coupling"
    dataset = open_dataset(name, _test_data_dir)

    analysis = ZZCouplingCouplerAnalysis(
        name, ["zz_coupling"], active_qubit="q12", spectator_qubit="q13"
    )
    qoi = analysis.process_coupler(dataset, "q12_q13")
    zz_coupling = qoi.analysis_result["zz_coupling"]["value"]

    assert qoi.analysis_successful
    assert pytest.approx(zz_coupling) == -15775.9096865654


@with_redis(_redis_values)
def test_plotting():
    """
    Test that the plotter produces a figure with the right number of axes
    """
    name = "zz_coupling"
    dataset = open_dataset(name, _test_data_dir)

    analysis = ZZCouplingCouplerAnalysis(
        name, ["zz_coupling"], active_qubit="q12", spectator_qubit="q13"
    )

    figures_dictionary = {}

    analysis.process_coupler(dataset, "q12_q13")
    analysis.plotter(figures_dictionary)

    assert "q12_q13" in figures_dictionary

    figure = figures_dictionary["q12_q13"][0]

    # 1 for spectator_qubit at |0> and 1 for spectator_qubit at |1>:
    assert len(figure.get_axes()) == 2
