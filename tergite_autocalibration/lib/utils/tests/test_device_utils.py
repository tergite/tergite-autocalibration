# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024, 2026
# (C) Chalmers Next Labs
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import math
import os

import numpy
import pytest

from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.lib.utils.device import DeviceConfiguration
from tergite_autocalibration.lib.utils.validators import (
    get_batched_dimensions,
    get_number_of_batches,
    reduce_batch,
)
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.tests.utils.fixtures import get_fixture_path

redis_mock = get_fixture_path("redis", "standard_redis_mock.json")


@with_redis(redis_mock)
def test_create_serial_device():
    device_manager = DeviceConfiguration(CONFIG.run.qubits, CONFIG.run.couplers)
    test_device = device_manager.configure_device("test_device")

    q00 = test_device.get_element("q00")
    pi_amplitude = q00.rxy.amp180()
    q00_q01 = test_device.get_edge("q00_q01")
    parking_current = q00_q01.cz.parking_current()

    assert test_device.elements() == CONFIG.run.qubits
    assert test_device.edges() == CONFIG.run.couplers

    assert math.isclose(pi_amplitude, 0.7308488204080522)
    assert math.isclose(parking_current, 0.00095)

    device_manager.close_device()


def test_save_serial_device(tmp_path):
    device_manager = DeviceConfiguration(CONFIG.run.qubits, CONFIG.run.couplers)
    test_device = device_manager.configure_device("test_device")
    device_manager.save_serial_device(test_device, data_path=tmp_path)
    device_name = test_device.name

    assert os.path.exists(os.path.join(tmp_path, f"{device_name}.json"))

    device_manager.close_device()


# NOTE: batching is not supported anymore, but maybe useful in the future
def test_batched_samplespaces():
    batched_samplespace = {
        "frequencies": {
            "q01": [numpy.linspace(3.0e9, 3.1e9, 11), numpy.linspace(3.1e9, 3.2e9, 11)],
            "q02": [numpy.linspace(3.3e9, 3.4e9, 11), numpy.linspace(3.4e9, 3.5e9, 11)],
            "q03": [numpy.linspace(3.5e9, 3.6e9, 11), numpy.linspace(3.6e9, 3.7e9, 11)],
        }
    }
    not_batched_samplespace = {
        "frequencies": {
            "q01": numpy.linspace(3.0e9, 3.1e9, 11),
            "q02": numpy.linspace(3.3e9, 3.4e9, 11),
            "q03": numpy.linspace(3.5e9, 3.6e9, 11),
        }
    }
    number_of_bathes_correct = get_number_of_batches(batched_samplespace)
    assert number_of_bathes_correct == 2

    with pytest.raises(TypeError) as err_info:
        get_number_of_batches(not_batched_samplespace)
        raise TypeError("Invalid samplespace type")

    assert err_info.type is TypeError
    assert get_batched_dimensions(batched_samplespace) == [
        "frequenciesq01",
        "frequenciesq02",
        "frequenciesq03",
    ]
    reduced_space = reduce_batch(batched_samplespace, 0)
    assert len(reduced_space["frequencies"]["q01"]) == 11
    assert len(reduced_space["frequencies"]["q02"]) == 11
    assert len(reduced_space["frequencies"]["q03"]) == 11
