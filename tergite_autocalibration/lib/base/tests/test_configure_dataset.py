# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.lib.nodes.characterization.randomized_benchmarking.node import (
    RandomizedBenchmarkingNode,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrization.node import (
    CZParametrizationNode,
)
from tergite_autocalibration.lib.nodes.coupler.spectroscopy.node import (
    QubitSpectroscopyVsCurrentNode,
)
from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.node import (
    ResonatorSpectroscopyNode,
)
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.tests.utils.fixtures import get_fixture_path
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon

redis_mock = get_fixture_path("redis", "standard_redis_mock.json")


def test_configure_dataset_qubits():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = ResonatorSpectroscopyNode("resonator_spectroscopy", CONFIG.run.qubits)

    raw_ds = node.generate_dummy_dataset()

    qubit_set = list(set(CONFIG.run.qubits))
    samplespace_freqs_00 = node.schedule_samplespace["ro_frequencies"]["q00"]

    configured_ds = node.configure_dataset(raw_ds)

    # check ds properties
    assert qubit_set == configured_ds.attrs["elements"]
    assert len(configured_ds.data_vars) == 2
    # check data_var properties
    assert configured_ds["yq00"].attrs["qubit"] == "q00"
    assert configured_ds["yq00"].values.shape == samplespace_freqs_00.shape
    # check coord properties
    assert configured_ds.coords["ro_frequenciesq00"].attrs["element_type"] == "qubit"

    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = ResonatorSpectroscopyNode("resonator_spectroscopy", CONFIG.run.qubits)

    raw_ds = node.generate_dummy_dataset()

    qubit_set = list(set(CONFIG.run.qubits))
    samplespace_freqs_00 = node.schedule_samplespace["ro_frequencies"]["q00"]

    configured_ds = node.configure_dataset(raw_ds)

    # check ds properties
    assert qubit_set == configured_ds.attrs["elements"]
    assert len(configured_ds.data_vars) == 2
    # check data_var properties
    assert configured_ds["yq00"].attrs["qubit"] == "q00"
    assert configured_ds["yq00"].values.shape == samplespace_freqs_00.shape
    # check coord properties
    assert configured_ds.coords["ro_frequenciesq00"].attrs["element_type"] == "qubit"


def test_configure_dataset_couplers():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node_0 = QubitSpectroscopyVsCurrentNode("coupler_anticrossing", CONFIG.run.couplers)
    node_0.this_current = 5e-6

    raw_ds = node_0.generate_dummy_dataset()

    coupler_set = list(set(CONFIG.run.couplers))
    samplespace_freqs_00 = node_0.schedule_samplespace["spec_frequencies"]["q00"]

    configured_ds = node_0.configure_dataset(raw_ds)

    # check ds properties
    assert coupler_set == configured_ds.attrs["elements"]
    assert len(configured_ds.data_vars) == 2 * len(coupler_set)
    # check data_var properties
    assert configured_ds["yq00"].attrs["qubit"] == "q00"
    assert configured_ds["yq00"].attrs["element"] == "q00_q01"
    assert configured_ds["yq00"].values.shape == samplespace_freqs_00.shape
    # check coord properties
    assert configured_ds.coords["spec_frequenciesq00"].attrs["element_type"] == "qubit"


def test_configure_dataset_qubits_with_loops():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = RandomizedBenchmarkingNode("randomized_benchmarking", CONFIG.run.qubits)

    raw_ds = node.generate_dummy_dataset()

    qubit_set = list(set(CONFIG.run.qubits))
    samplespace_cliffords_00 = node.schedule_samplespace["number_of_cliffords"]["q00"]
    number_of_cliffords_00 = len(samplespace_cliffords_00)

    configured_ds = node.configure_dataset(raw_ds)

    # check ds properties
    assert qubit_set == configured_ds.attrs["elements"]
    assert len(configured_ds.data_vars) == 2
    # check data_var properties
    assert configured_ds["yq00"].attrs["qubit"] == "q00"
    assert configured_ds["yq00"].values.shape == (number_of_cliffords_00, node.loops)
    # check coord properties
    ds_coords = configured_ds.coords
    assert ds_coords["number_of_cliffordsq00"].attrs["element_type"] == "qubit"
    assert "loops" in configured_ds.coords
    assert configured_ds.coords["loops"].size == node.loops


@with_redis(redis_mock)
def test_configure_dataset_qubits_with_3state_discrimination():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = CZParametrizationNode(
        "cz_parametrization", CONFIG.run.qubits, CONFIG.run.couplers
    )
    coupler_set = list(set(CONFIG.run.couplers))
    samplespace_cz_ampls_00_01 = node.schedule_samplespace["cz_pulse_amplitudes"][
        "q00_q01"
    ]
    samplespace_cz_freqs_00_01 = node.schedule_samplespace["cz_pulse_frequencies"][
        "q00_q01"
    ]
    number_of_cz_ampls_00_01 = len(samplespace_cz_ampls_00_01)
    number_of_cz_freqs_00_01 = len(samplespace_cz_freqs_00_01)

    raw_ds = node.generate_dummy_dataset()

    configured_ds = node.configure_dataset(raw_ds)
    # check ds properties
    assert coupler_set == configured_ds.attrs["elements"]
    assert len(configured_ds.data_vars) == 2 * len(coupler_set)
    # check data_var properties
    assert configured_ds["yq00"].attrs["qubit"] == "q00"
    assert configured_ds["yq00"].attrs["element"] == "q00_q01"
    assert configured_ds["yq00"].values.shape == (
        number_of_cz_ampls_00_01,
        number_of_cz_freqs_00_01,
        node.loops,
    )
    # check coord properties
    assert (
        configured_ds.coords["cz_pulse_amplitudesq00_q01"].attrs["element_type"]
        == "coupler"
    )
