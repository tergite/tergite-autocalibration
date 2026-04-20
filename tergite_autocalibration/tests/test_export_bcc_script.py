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

import os

import toml

from tergite_autocalibration.scripts.export_to_bcc import export
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.tests.utils.fixtures import get_fixture_path

_redis_backup_path = get_fixture_path("redis", "export_bcc_script.json")
_config_path = get_fixture_path("templates", "q11_q12")


@with_redis(_redis_backup_path)
def test_export_bcc_script(tmp_path):
    """
    Check whether results are equal to mock values
    """
    output_path_ = os.path.join(tmp_path, "calibration_seed.toml")
    export(["q11", "q12"], ["q11_q12"], output_path=output_path_)

    with open(output_path_, "r") as f:
        output_loaded_values = toml.load(f)

    with open(get_fixture_path("configs", "calibration_seed.toml"), "r") as f:
        expected_output_values = toml.load(f)

    assert output_loaded_values == expected_output_values


@with_redis(_redis_backup_path)
def test_export_bcc_script_partial(tmp_path):
    """
    Check whether results are equal to mock values
    """
    output_path_ = os.path.join(tmp_path, "calibration_seed.toml")
    export(["q11"], [], output_path=output_path_)

    with open(output_path_, "r") as f:
        output_loaded_values = toml.load(f)

    assert output_loaded_values["calibration_config"]["coupler"] == []
    assert len(output_loaded_values["calibration_config"]["qubit"]) == 1
    assert output_loaded_values["calibration_config"]["qubit"][0]["id"] == "q11"
