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

import json
import os
import sys

from quantify_scheduler.backends.qblox_backend import QbloxHardwareCompilationConfig


def migrate_qblox_hardware_configuration(file_path_):
    # Load the hardware configuration
    with open(file_path_, "r") as file_:
        hardware_config_transmon_old_style = json.load(file_)

    # Migrate to the new structure of the hardware configuration
    hardware_config_transmon_new_style = QbloxHardwareCompilationConfig.model_validate(
        hardware_config_transmon_old_style
    )

    # Serialize the hardware configuration object
    serialized_config = hardware_config_transmon_new_style.model_dump_json(
        exclude_unset=True
    )

    # Let the output file path be the same as the input
    base, ext = os.path.splitext(file_path_)
    new_file_path = f"{base}_new_auto_migrated{ext}"

    # Write the hardware configuration to the new file
    with open(new_file_path, "w") as file_:
        json.dump(json.loads(serialized_config), file_, indent=4)

    print(f"File saved as: {new_file_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python migrate_qblox_hardware_configuration.py <file_path>")
    else:
        file_path = sys.argv[1]
        migrate_qblox_hardware_configuration(file_path)
