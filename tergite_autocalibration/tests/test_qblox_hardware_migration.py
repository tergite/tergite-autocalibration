# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os.path

from tergite_autocalibration.scripts.migrate_qblox_hardware_configuration import (
    migrate_qblox_hardware_configuration,
)
from tergite_autocalibration.tests.utils.fixtures import load_fixture, _FIXTURES_PATH


def test_qblox_hardware_migration():
    # Path to the old hardware configuration
    path_to_hardware_config_old = os.path.join(
        _FIXTURES_PATH, "configs", "hardware_config_old.json"
    )

    # Migrate using the function
    migrate_qblox_hardware_configuration(path_to_hardware_config_old)

    # Load the migrated configuration and the correct new configuration
    migrated_config = load_fixture(
        "configs/hardware_config_old_new_auto_migrated.json", fmt="json"
    )
    hardware_config = load_fixture(
        "configs/hardware_config_migration_mock.json", fmt="json"
    )

    assert hardware_config == migrated_config

    # Clean up the generated content
    path_to_hardware_config_auto_migrated = os.path.join(
        _FIXTURES_PATH, "configs", "hardware_config_old_new_auto_migrated.json"
    )
    os.remove(path_to_hardware_config_auto_migrated)
