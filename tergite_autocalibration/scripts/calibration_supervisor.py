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
# Modified:
#
# - Martin Ahindura, 2023

from ipaddress import IPv4Address
from typing import List, Union

import toml
from colorama import Fore, Style
from colorama import init as colorama_init
from qblox_instruments import Cluster
from qblox_instruments.types import ClusterType
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent

from tergite_autocalibration.config import settings
from tergite_autocalibration.config.settings import (
    CLUSTER_IP,
    CLUSTER_NAME,
    REDIS_CONNECTION,
)
from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.lib.utils.graph import filtered_topological_order
from tergite_autocalibration.lib.utils.node_factory import NodeFactory
from tergite_autocalibration.utils.dataset_utils import create_node_data_path
from tergite_autocalibration.utils.dto.enums import DataStatus, MeasurementMode
from tergite_autocalibration.utils.logger.errors import ClusterNotFoundError
from tergite_autocalibration.utils.logger.tac_logger import logger
from tergite_autocalibration.utils.logger.visuals import draw_arrow_chart
from tergite_autocalibration.utils.redis_utils import (
    populate_initial_parameters,
    populate_node_parameters,
    populate_quantities_of_interest,
)
from tergite_autocalibration.utils.user_input import (
    attenuation_setting,
    user_requested_calibration,
)

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
    calibration_node_factory = NodeFactory()

    def __init__(
        self,
        measurement_mode: "MeasurementMode",
        cluster_ip: Union[str, "IPv4Address"] = CLUSTER_IP,
        cluster_timeout: int = 222,
        node_name="",
        data_path="",
    ) -> None:
        # Read hardware related configuration steps
        self.measurement_mode: "MeasurementMode" = measurement_mode
        self.cluster_ip: Union[str, "IPv4Address"] = cluster_ip
        self.cluster_timeout: int = cluster_timeout

        # Create objects to communicate with the hardware
        self.cluster: "Cluster" = self._create_cluster()
        self.lab_ic: "InstrumentCoordinator" = self._create_lab_ic(self.cluster)

        # TODO: user configuration could be a toml file
        # Read the calibration specific parameters
        self.qubits = user_requested_calibration["all_qubits"]
        self.couplers = user_requested_calibration["couplers"]
        self.target_node = user_requested_calibration["target_node"]
        self.user_samplespace = user_requested_calibration["user_samplespace"]

        # Read the device configuration
        self.transmon_configuration = toml.load(settings.DEVICE_CONFIG)

        # Initialize the node structure
        self.topo_order = filtered_topological_order(self.target_node)

    def _create_cluster(self) -> "Cluster":
        cluster_: "Cluster"
        if self.measurement_mode == MeasurementMode.real:
            Cluster.close_all()
            try:
                cluster_ = Cluster(CLUSTER_NAME, str(self.cluster_ip))
            except ConnectionRefusedError:
                msg = "Cluster is disconnected. Maybe it has crushed? Try flick it off and on"
                print("-" * len(msg))
                print(f"{Fore.LIGHTRED_EX}{Style.BRIGHT}{msg}{Style.RESET_ALL}")
                print("-" * len(msg))
                quit()
            print(
                f" \n\u26A0 {Fore.MAGENTA}{Style.BRIGHT}Reseting Cluster at IP *{str(self.cluster_ip)[-3:]}{Style.RESET_ALL}\n"
            )
            cluster_.reset()
            return cluster_
        else:
            Cluster.close_all()
            dummy_setup = {str(mod): ClusterType.CLUSTER_QCM_RF for mod in range(1, 16)}
            dummy_setup["16"] = ClusterType.CLUSTER_QRM_RF
            dummy_setup["17"] = ClusterType.CLUSTER_QRM_RF
            cluster_ = Cluster(CLUSTER_NAME, dummy_cfg=dummy_setup)
            # raise ClusterNotFoundError(
            #     f"Cannot create cluster object from {self.cluster_ip}"
            # )
            return cluster_

    def _create_lab_ic(self, clusters: Union["Cluster", List["Cluster"]]):
        ic_ = InstrumentCoordinator("lab_ic")
        if isinstance(clusters, Cluster):
            clusters = [clusters]
        for cluster in clusters:
            # Set the attenuation values for the modules
            for module in cluster.modules:
                try:
                    if module.is_qcm_type and module.is_rf_type:
                        module.out0_att(attenuation_setting["qubit"])  # Control lines
                        # print(f'Attenuation setting for {module.name} is {attenuation_setting["qubit"]}')
                        module.out1_att(attenuation_setting["coupler"])  # Flux lines
                        # print(f'Attenuation setting for {module.name} is {attenuation_setting["coupler"]}')
                    elif module.is_qrm_type and module.is_rf_type:
                        module.out0_att(attenuation_setting["readout"])  # Readout lines
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

        # TODO: check if coupler node status throws error after REDISFLUSHALL
        populate_quantities_of_interest(
            self.topo_order,
            self.qubits,
            self.couplers,
            self.calibration_node_factory,
            REDIS_CONNECTION,
        )
        #        populate_active_reset_parameters(
        #            self.transmon_configuration, self.qubits, REDIS_CONNECTION
        #        )

        for calibration_node in self.topo_order:
            self.inspect_node(calibration_node)
            logger.info(f"{calibration_node} node is completed")

    def inspect_node(self, node_name: str):
        # TODO: this function must be split
        logger.info(f"Inspecting node {node_name}")
        populate_initial_parameters(
            self.transmon_configuration, self.qubits, self.couplers, REDIS_CONNECTION
        )
        if node_name in [
            "coupler_spectroscopy",
            "cz_chevron",
            "cz_chevron_amplitude",
            "cz_calibration",
            "cz_calibration_ssro",
            "cz_calibration_swap_ssro",
            "cz_dynamic_phase",
            "cz_dynamic_phase_swap",
            "tqg_randomized_benchmarking",
            "tqg_randomized_benchmarking_interleaved",
        ]:
            coupler_statuses = [
                REDIS_CONNECTION.hget(f"cs:{coupler}", node_name) == "calibrated"
                for coupler in self.couplers
            ]

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
            self.transmon_configuration,
            self.qubits,
            self.couplers,
            REDIS_CONNECTION,
        )

        # Check Redis if node is calibrated
        status = DataStatus.undefined

        if node_name in [
            "coupler_spectroscopy",
            "cz_chevron",
            "cz_chevron_duration_single_shots_experimental",
            "cz_calibration_single_shots_experimental",
            "cz_chevron_experimental",
            "cz_optimize_chevron",
            "cz_chevron_amplitude",
            "cz_calibration",
            "cz_calibration_ssro",
            "cz_calibration_swap_ssro",
            "cz_dynamic_phase",
            "cz_dynamic_phase_swap",
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
                    raise ValueError(f"status: {status}")
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
                    raise ValueError(f"status: {status}")

        if status == DataStatus.in_spec:
            print(
                f" \u2714  {Fore.GREEN}{Style.BRIGHT}Node {node_name} in spec{Style.RESET_ALL}"
            )
            return

        elif status == DataStatus.out_of_spec:
            print(
                "\u2691\u2691\u2691 "
                + f"{Fore.RED}{Style.BRIGHT}Calibration required for Node {node_name}{Style.RESET_ALL}"
            )

            node: BaseNode = self.calibration_node_factory.create_node(
                node_name,
                self.qubits,
                couplers=self.couplers,
                measurement_mode=self.measurement_mode,
            )
            if node.name in self.user_samplespace:
                update_to_user_samplespace(node, self.user_samplespace)
            # it's maybe useful to give access to the ic
            node.lab_instr_coordinator = self.lab_ic

            logger.info(f"Calibrating node {node.name}")
            # TODO: This could be in the node initializer
            data_path = create_node_data_path(node)
            measurement_result = node.calibrate(data_path, self.measurement_mode)

            # TODO:  develop failure strategies ->
            # if node_calibration_status == DataStatus.out_of_spec:
            #     node_expand()
            #     node_calibration_status = self.calibrate_node(node)
