# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2026
# (C) Chalmers Next Labs 2026
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
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.analysis import (
    CZChevronAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.measurement import (
    CZChevronMeasurement,
)
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.node import CZChevronNode
from tergite_autocalibration.lib.nodes.schedule_node import OuterScheduleNode
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


def test_node_creation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    coupler = "q13_q14"
    REDIS_CONNECTION.hset(f"couplers:{coupler}", "parking_current", "100e-6")
    REDIS_CONNECTION.hset(f"transmons:{'q13'}", "clock_freqs:f01", "4.2e6")
    REDIS_CONNECTION.hset(f"transmons:{'q13'}", "clock_freqs:f12", "4.0e6")
    REDIS_CONNECTION.hset(f"transmons:{'q14'}", "clock_freqs:f01", "5.2e6")
    REDIS_CONNECTION.hset(f"transmons:{'q14'}", "clock_freqs:f12", "5.0e6")
    REDIS_CONNECTION.hset(f"couplers:{'q13_q14'}", "cz_pulse_frequency", "7.16e8")
    node = CZChevronNode(
        all_qubits=["q13", "q14"],
        couplers=[coupler],
    )
    assert isinstance(node, CouplerNode)


def test_class_attribute_objects():
    REDIS_CONNECTION.hset(f"couplers:{'q13_q14'}", "cz_pulse_frequency", "7.16e8")
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = CZChevronNode(all_qubits=["q13", "q14"], couplers=["q13_q14"])
    assert isinstance(node.measurement_obj, type(CZChevronMeasurement))
    assert isinstance(node.analysis_obj, type(CZChevronAnalysis))
    assert issubclass(node.measurement_type, OuterScheduleNode)


def test_dummy_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    for coupler in CONFIG.run.couplers:
        REDIS_CONNECTION.hset(f"couplers:{coupler}", "parking_current", "100e-6")
        REDIS_CONNECTION.hset(f"couplers:{coupler}", "cz_pulse_frequency", "7.16e8")
    for qubit in CONFIG.run.qubits[::2]:
        REDIS_CONNECTION.hset(f"transmons:{qubit}", "clock_freqs:f01", "4.2e6")
        REDIS_CONNECTION.hset(f"transmons:{qubit}", "clock_freqs:f12", "4.0e6")
    for qubit in CONFIG.run.qubits[1::2]:
        REDIS_CONNECTION.hset(f"transmons:{qubit}", "clock_freqs:f01", "5.2e6")
        REDIS_CONNECTION.hset(f"transmons:{qubit}", "clock_freqs:f12", "5.0e6")

    node = CZChevronNode(CONFIG.run.couplers)
    dummy_dataset = node.generate_dummy_dataset()
    first_coupler = CONFIG.run.couplers[0]

    number_of_durations = len(
        node.schedule_samplespace["cz_pulse_durations"][first_coupler]
    )

    data_vars = dummy_dataset.data_vars

    assert len(data_vars) == 2 * len(CONFIG.run.couplers)
    assert data_vars[0].size == number_of_durations * node.loops
