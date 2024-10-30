import numpy
import pytest

# from tergite_autocalibration.lib.utils.device import configure_device
from tergite_autocalibration.lib.utils.validators import (
    get_batched_coord,
    get_number_of_batches,
    reduce_batch,
)


def test_device_configuration():
    name = "QPU_device"
    qubits = ["q01", "q02", "q03"]
    couplers = ["q01_q02"]
    # TODO: ----------------------------------------------------
    # TODO: For this to be tested a mock redis setup is required
    # TODO: ----------------------------------------------------


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

    assert get_batched_coord(batched_samplespace) == "frequencies"
    reduced_space = reduce_batch(batched_samplespace, 0)
    assert len(reduced_space["frequencies"]["q01"]) == 11
    assert len(reduced_space["frequencies"]["q02"]) == 11
    assert len(reduced_space["frequencies"]["q03"]) == 11
