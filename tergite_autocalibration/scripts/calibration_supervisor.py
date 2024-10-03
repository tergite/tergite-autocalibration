# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
#

from ipaddress import IPv4Address
from pathlib import Path
from typing import Union, List

import toml
from colorama import Fore
from colorama import Style
from colorama import init as colorama_init
from qblox_instruments import Cluster
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent

from tergite_autocalibration.config import settings
from tergite_autocalibration.config.data import dh
from tergite_autocalibration.config.settings import CLUSTER_IP, REDIS_CONNECTION
from tergite_autocalibration.config.settings import CLUSTER_NAME
from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.lib.utils.graph import filtered_topological_order
from tergite_autocalibration.lib.utils.node_factory import NodeFactory
from tergite_autocalibration.utils.dataset_utils import create_node_data_path
from tergite_autocalibration.utils.dto.enums import DataStatus
from tergite_autocalibration.utils.dto.enums import MeasurementMode
from tergite_autocalibration.utils.logger.errors import ClusterNotFoundError
from tergite_autocalibration.utils.logger.tac_logger import logger
from tergite_autocalibration.utils.redis_utils import (
    populate_initial_parameters,
    populate_node_parameters,
    populate_quantities_of_interest,
)
from tergite_autocalibration.utils.user_input import user_requested_calibration
from tergite_autocalibration.utils.visuals import draw_arrow_chart
from tergite_autocalibration.config.calibration import CONFIG

colorama_init()


def update_to_user_samplespace(node: BaseNode, user_samplespace: dict):
    node_user_samplespace = user_samplespace[node.name]
    for settable, element_samplespace in node_user_samplespace.items():
        if settable in node.schedule_samplespace:
            node.schedule_samplespace[settable] = element_samplespace
        elif settable in node.external_samplespace:
            node.external_samplespace[settable] = element_samplespace
        else:
            raise KeyError(f"{settable} not in any samplespace")
    return


class CalibrationSupervisor:
    def __init__(
        self,
        cluster_mode: "MeasurementMode" = MeasurementMode.real,
        cluster_ip: Union[str, "IPv4Address"] = CLUSTER_IP,
        cluster_timeout: int = 222,
        node_name="",
        data_path="",
    ) -> None:
        # Read hardware related configuration steps
        self.cluster_mode: "MeasurementMode" = cluster_mode
        self.cluster_ip: Union[str, "IPv4Address"] = cluster_ip
        self.cluster_timeout: int = cluster_timeout
        self.node_name_to_re_analyse = node_name
        self.data_path = Path(data_path)
        self.lab_ic = ""

        # Create objects to communicate with the hardware
        if self.cluster_mode == MeasurementMode.re_analyse:
            logger.info(
                "Cluster will not be defined as there is no need to take a measurement in re-analysis mode."
            )
        else:
            self.cluster: "Cluster" = self._create_cluster()
            self.lab_ic: "InstrumentCoordinator" = self._create_lab_ic(self.cluster)

        # TODO: user configuration could be a toml file
        # Read the calibration specific parameters
        self.qubits = CONFIG.qubits
        self.couplers = CONFIG.couplers
        self.target_node = CONFIG.target_node
        self.user_samplespace = user_requested_calibration["user_samplespace"]
        self.measurement_mode = self.cluster_mode

        # Initialize the node structure
        self.node_factory = NodeFactory()
        self.topo_order = filtered_topological_order(CONFIG.target_node)

    def _create_cluster(self) -> "Cluster":
        cluster_: "Cluster"
        if self.cluster_mode == MeasurementMode.real:
            Cluster.close_all()
            cluster_ = Cluster(CLUSTER_NAME, str(self.cluster_ip))
            cluster_.reset()
            logger.info(f"Reseting Cluster at IP *{str(self.cluster_ip)[-3:]}")
            return cluster_
        else:
            raise ClusterNotFoundError(
                f"Cannot create cluster object from {self.cluster_ip}"
            )

    def _create_lab_ic(self, clusters: Union["Cluster", List["Cluster"]]):
        ic_ = InstrumentCoordinator("lab_ic")
        if isinstance(clusters, Cluster):
            clusters = [clusters]
        for cluster in clusters:
            # Set the attenuation values for the modules
            for module in cluster.modules:
                try:
                    if module.is_qcm_type and module.is_rf_type:
                        module.out0_att(dh.get_legacy("attenuation_setting")["qubit"])  # Control lines
                        # print(f'Attenuation setting for {module.name} is {attenuation_setting["qubit"]}')
                        module.out1_att(dh.get_legacy("attenuation_setting")["coupler"])  # Flux lines
                        # print(f'Attenuation setting for {module.name} is {attenuation_setting["coupler"]}')
                    elif module.is_qrm_type and module.is_rf_type:
                        module.out0_att(dh.get_legacy("attenuation_setting")["readout"])  # Readout lines
                        # print(
                        #     f'Attenuation setting for {module.name} is {attenuation_setting["readout"]}'
                        # )
                except:
                    pass
            ic_.add_component(ClusterComponent(cluster))
            ic_.timeout(self.cluster_timeout)
        return ic_

    def calibrate_system(self):
        # TODO: everything which is not in the inspect or calibrate function should go here
        logger.info("Starting System Calibration")
        number_of_qubits = len(self.qubits)
        draw_arrow_chart(f"Qubits: {number_of_qubits}", self.topo_order)

        populate_quantities_of_interest(
            self.qubits, self.couplers, REDIS_CONNECTION
        )

        for calibration_node in self.topo_order:
            self.inspect_node(calibration_node)
            logger.info(f"{calibration_node} node is completed")

    def inspect_node(self, node_name: str):
        # TODO: the inspect node function could be part of the node
        logger.info(f"Inspecting node {node_name}")

        node: BaseNode = self.node_factory.create_node(
            node_name, self.qubits, couplers=self.couplers
        )

        if node.name in self.user_samplespace:
            update_to_user_samplespace(node, self.user_samplespace)

        # some nodes e.g. cw spectroscopy needs access to the instruments
        node.lab_instr_coordinator = self.cluster_ip

        logger.info(
            "Initialising paramaters for qubits: "
            + str(self.qubits)
            + " and couplers: "
            + str(self.couplers)
        )
        populate_initial_parameters(
            self.qubits, self.couplers, REDIS_CONNECTION
        )
        # print(f'{node_name = }')
        # print(f'{self.couplers = }')
        if node_name in [
            "coupler_spectroscopy",
            "cz_chevron",
            "cz_chevron_amplitude",
            "cz_calibration",
            "cz_calibration_ssro",
            "cz_calibration_swap_ssro",
            "cz_dynamic_phase",
            "cz_dynamic_phase_swap",
            "cz_parametrisation_fix_duration",
            "tqg_randomized_benchmarking",
            "tqg_randomized_benchmarking_interleaved",
        ]:
            coupler_statuses = [
                REDIS_CONNECTION.hget(f"cs:{coupler}", node_name) == "calibrated"
                for coupler in self.couplers
            ]
            # print(f'{coupler_statuses=}')
            # node is calibrated only when all couplers have the node calibrated:
            is_node_calibrated = all(coupler_statuses)
        else:
            qubits_statuses = [
                REDIS_CONNECTION.hget(f"cs:{qubit}", node_name) == "calibrated"
                for qubit in self.qubits
            ]
            # node is calibrated only when all qubits have the node calibrated:
            is_node_calibrated = all(qubits_statuses)

        populate_node_parameters(
            node_name,
            is_node_calibrated,
            self.qubits,
            self.couplers,
            REDIS_CONNECTION,
        )

        # Check Redis if node is calibrated
        status = DataStatus.undefined

        if node_name in [
            "coupler_spectroscopy",
            "cz_chevron",
            "cz_optimize_chevron",
            "cz_chevron_amplitude",
            "cz_calibration",
            "cz_calibration_ssro",
            "cz_calibration_swap_ssro",
            "cz_dynamic_phase",
            "cz_dynamic_phase_swap",
            "cz_parametrisation_fix_duration",
            "tqg_randomized_benchmarking",
            "tqg_randomized_benchmarking_interleaved",
        ]:
            for coupler in self.couplers:
                # the calibrated, not_calibrated flags may be not necessary,
                # just store the DataStatus on Redis
                is_calibrated = REDIS_CONNECTION.hget(f"cs:{coupler}", node_name)
                if is_calibrated == "not_calibrated":
                    status = DataStatus.out_of_spec
                    break  # even if a single qubit is not_calibrated mark as out_of_spec
                elif is_calibrated == "calibrated":
                    status = DataStatus.in_spec
                else:
                    raise ValueError(
                        f"REDIS error: cannot find cs:{coupler}", node_name
                    )
        else:
            for qubit in self.qubits:
                # the calibrated, not_calibrated flags may be not necessary,
                # just store the DataStatus on Redis
                is_calibrated = REDIS_CONNECTION.hget(f"cs:{qubit}", node_name)
                if is_calibrated == "not_calibrated":
                    status = DataStatus.out_of_spec
                    break  # even if a single qubit is not_calibrated mark as out_of_spec
                elif is_calibrated == "calibrated":
                    status = DataStatus.in_spec
                else:
                    raise ValueError(f"REDIS error: cannot find cs:{qubit}", node_name)

        print(node_name)
        print(self.node_name_to_re_analyse)
        if (
            self.measurement_mode == MeasurementMode.re_analyse
            and node_name == self.node_name_to_re_analyse
        ):
            print(
                "\u2691\u2691\u2691 "
                + f"{Fore.RED}{Style.BRIGHT}Calibration required for Node {node_name}{Style.RESET_ALL}"
            )
            logger.info(f"Calibrating node {node.name}")
            # TODO: This could be in the node initializer
            node.calibrate(self.data_path, self.lab_ic, self.measurement_mode)

        elif status == DataStatus:
            print(
                f" \u2714  {Fore.GREEN}{Style.BRIGHT}Node {node_name} in spec{Style.RESET_ALL}"
            )
            return

        elif status == DataStatus.out_of_spec:
            print(
                "\u2691\u2691\u2691 "
                + f"{Fore.RED}{Style.BRIGHT}Calibration required for Node {node_name}{Style.RESET_ALL}"
            )
            logger.info(f"Calibrating node {node.name}")
            # TODO: This could be in the node initializer
            data_path = create_node_data_path(node)
            node.calibrate(data_path, self.lab_ic, self.measurement_mode)

            # TODO : develop failure strategies ->
            # if node_calibration_status == DataStatus.out_of_spec:
            #     node_expand()
            #     node_calibration_status = self.calibrate_node(node)
