# This code is part of Tergite
#
# (C) Copyright Abdullah-Al Amin 2023
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
#
# Modified:
#
# - Martin Ahindura, 2023
# - Stefan Hill, 2024
#
# NOTE: This updater is coming from tergite-bcc and a copy exists there as well.
# Please make sure to update both files, if you are changing one of them!

import json
from pathlib import Path

import requests
import toml

from tergite_autocalibration.config.globals import ENV
from tergite_autocalibration.tools.mss.convert import store_manual_parameters
from tergite_autocalibration.tools.mss.storage import get_component_value
from tergite_autocalibration.utils.logging import logger

BACKEND_CONFIG = Path(__file__).parent / "backend_config_default.toml"

mss_url = str(ENV.mss_machine_root_url)


def create_backend_snapshot() -> dict:
    """Creates a dict containing the properties of this backend

    This dictionary is later saved in the MSS storage by
    PUTing it to the `/backends` MSS endpoint
    """
    with open(BACKEND_CONFIG, "r") as f:
        config = toml.load(f)
        general_config = config["general_config"]
        qubit_ids = config["device_config"]["qubit_ids"]
        qubit_parameters = config["device_config"]["qubit_parameters"]
        resonator_parameters = config["device_config"]["resonator_parameters"]
        discriminator_parameters = config["device_config"]["discriminator_parameters"][
            "lda_parameters"
        ]
        coupling_map = config["device_config"]["coupling_map"]
        meas_map = config["device_config"]["meas_map"]
        gate_configs = config["gates"]

    # updating and constructing components
    qubits = []
    resonators = []
    lda_discriminators = {}

    for qubit_id in qubit_ids:
        id = str(qubit_id).strip("q")

        store_manual_parameters(qubit_id)

        qubit = {}
        for parameter in qubit_parameters:
            if parameter == "id":
                value = qubit_id
            else:
                # reading the component parameter values in redis
                value = get_component_value("qubit", parameter, id)
            qubit.update({parameter: value})
        qubits.append(qubit)

        resonator = {}
        for parameter in resonator_parameters:
            if parameter == "id":
                value = qubit_id
            else:
                # reading the component parameter values in redis
                value = get_component_value("readout_resonator", parameter, id)
            resonator.update({parameter: value})
        resonators.append(resonator)

        # Here, we are doing it only for lda
        lda_discriminators[qubit_id] = {
            parameter: get_component_value("discriminator", parameter, id)
            for parameter in discriminator_parameters
        }

    # more components, like couplers etc. can be added in similar manner and added
    # to the device_properties dict ....

    device_properties = {
        "device_properties": {**{"qubit": qubits}, **{"readout_resonator": resonators}}
    }
    return {
        **general_config,
        **{"qubit_ids": qubit_ids},
        **device_properties,
        **{"discriminators": {"lda": lda_discriminators}},
        **{"coupling_map": coupling_map},
        **{"meas_map": meas_map},
        **{"gates": gate_configs},
    }


def update_mss(collection: str = None):
    """Pushes the snapshot of this backend to the given collection in MSS"""
    current_backend_snapshot = create_backend_snapshot()
    backend_snapshot_json = json.dumps(current_backend_snapshot, indent=4)
    if collection:
        response = requests.put(
            mss_url + f"/backends?collection={collection}", backend_snapshot_json
        )
    else:
        response = requests.put(mss_url + "/backends", backend_snapshot_json)

    if response:
        logger.status(
            f"'{current_backend_snapshot['name']}' backend configuration is sent to mss"
        )
    else:
        logger.status(
            f"Could not send '{current_backend_snapshot['name']} 'backend configuration to mss"
        )


if __name__ == "__main__":
    # convert_all_redis_values()
    update_mss()
