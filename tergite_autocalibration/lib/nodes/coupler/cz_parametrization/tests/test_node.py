# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2024
# (C) Copyright Michele Eleftherios Moschandreou 2025
# (C) Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import pytest

from tergite_autocalibration.config.globals import CONFIG, REDIS_CONNECTION
from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.coupler.cz_parametrization.analysis import (
    CZParametrizationAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrization.measurement import (
    CZParametrizationMeasurement,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrization.node import (
    CZParametrizationNode,
)
from tergite_autocalibration.lib.nodes.external_parameter_node import (
    ExternalParameterNode,
)
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


def test_cannotCreateCorrectType():
    """
    raise error if parking current does not exist on redis
    """
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    coupler = "q14_q15"
    if REDIS_CONNECTION.hexists(f"couplers:{coupler}", "parking_current"):
        REDIS_CONNECTION.hdel(f"couplers:{coupler}", "parking_current")

    with pytest.raises(TypeError):
        CZParametrizationNode(all_qubits=["q14", "q15"], couplers=["q14_q15"])


def test_canCreateCorrectType():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    coupler = "q14_q15"
    REDIS_CONNECTION.hset(f"couplers:{coupler}", "parking_current", "100e-6")
    REDIS_CONNECTION.hset(f"transmons:{'q14'}", "clock_freqs:f01", "4.2e6")
    REDIS_CONNECTION.hset(f"transmons:{'q14'}", "clock_freqs:f12", "4.0e6")
    REDIS_CONNECTION.hset(f"transmons:{'q15'}", "clock_freqs:f01", "5.2e6")
    REDIS_CONNECTION.hset(f"transmons:{'q15'}", "clock_freqs:f12", "5.0e6")
    node = CZParametrizationNode(
        all_qubits=["q14", "q15"],
        couplers=[coupler],
    )
    assert isinstance(node, CouplerNode)


def test_ValidationReturnErrorWithSameQubitCoupler():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    with pytest.raises(ValueError):
        CZParametrizationNode(all_qubits=["q14", "q15"], couplers=["q14_q14"])


@pytest.mark.skip
def test_ValidationReturnErrorWithQubitsNotMatchingCouplers():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    with pytest.raises(ValueError):
        CZParametrizationNode(all_qubits=["q14", "q16"], couplers=["q14_q15"])


def test_MeasurementClassType():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    c = CZParametrizationNode(all_qubits=["q14", "q15"], couplers=["q14_q15"])
    assert isinstance(c.measurement_obj, type(CZParametrizationMeasurement))
    assert isinstance(c.analysis_obj, type(CZParametrizationAnalysis))
    assert issubclass(c.measurement_type, ExternalParameterNode)


def test_dummy_01_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    for coupler in CONFIG.run.couplers:
        REDIS_CONNECTION.hset(f"couplers:{coupler}", "parking_current", "100e-6")
    for qubit in CONFIG.run.qubits[::2]:
        REDIS_CONNECTION.hset(f"transmons:{qubit}", "clock_freqs:f01", "4.2e6")
        REDIS_CONNECTION.hset(f"transmons:{qubit}", "clock_freqs:f12", "4.0e6")
    for qubit in CONFIG.run.qubits[1::2]:
        REDIS_CONNECTION.hset(f"transmons:{qubit}", "clock_freqs:f01", "5.2e6")
        REDIS_CONNECTION.hset(f"transmons:{qubit}", "clock_freqs:f12", "5.0e6")

    node = CZParametrizationNode(
        all_qubits=CONFIG.run.qubits, couplers=CONFIG.run.couplers
    )
    dummy_dataset = node.generate_dummy_dataset()
    first_coupler = CONFIG.run.couplers[0]

    number_of_frequencies = len(
        node.schedule_samplespace["cz_pulse_frequencies"][first_coupler]
    )
    number_of_amplitudes = len(
        node.schedule_samplespace["cz_pulse_amplitudes"][first_coupler]
    )

    data_vars = dummy_dataset.data_vars

    assert len(data_vars) == 2 * len(CONFIG.run.couplers)
    assert (
        data_vars[0].size == number_of_frequencies * number_of_amplitudes * node.loops
    )
