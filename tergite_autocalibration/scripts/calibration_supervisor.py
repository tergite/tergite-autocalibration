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

from dataclasses import dataclass, field
from ipaddress import IPv4Address
from pathlib import Path
from typing import Union, List

from colorama import Fore, Style
from colorama import init as colorama_init
from qblox_instruments import Cluster
from qblox_instruments.types import ClusterType
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent

from tergite_autocalibration.config.globals import REDIS_CONNECTION, CLUSTER_IP
from tergite_autocalibration.config.legacy import LEGACY_CONFIG, dh
from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.lib.utils.graph import filtered_topological_order
from tergite_autocalibration.lib.utils.node_factory import NodeFactory
from tergite_autocalibration.utils.backend.redis_utils import (
    populate_initial_parameters,
    populate_node_parameters,
    populate_quantities_of_interest,
)
from tergite_autocalibration.utils.dto.enums import DataStatus, MeasurementMode
from tergite_autocalibration.utils.io.dataset_utils import create_node_data_path
from tergite_autocalibration.utils.logger.tac_logger import logger
from tergite_autocalibration.utils.logger.visuals import draw_arrow_chart

colorama_init()


@dataclass
class CalibrationConfig:
    """
    Configuration settings for the calibration process.
    """

    cluster_mode: "MeasurementMode" = MeasurementMode.real
    cluster_ip: "IPv4Address" = CLUSTER_IP
    cluster_timeout: int = 222
    data_path: Path = Path("")
    qubits: List[str] = field(
        default_factory=lambda: user_requested_calibration["all_qubits"]
    )
    couplers: List[str] = field(
        default_factory=lambda: user_requested_calibration["couplers"]
    )
    target_node_name: str = user_requested_calibration["target_node"]
    user_samplespace: dict = field(
        default_factory=lambda: user_requested_calibration["user_samplespace"]
    )
    transmon_configuration: dict = field(
        default_factory=lambda: toml.load(settings.DEVICE_CONFIG)
    )


class HardwareManager:
    """
    Manages hardware setup, including initializing clusters and instrument coordinators.
    """

    def __init__(self, config: "CalibrationConfig") -> None:
        # Store the configuration settings and initialize the instrument coordinator
        self.config = config
        self.lab_ic = ""

        # Check if hardware setup is necessary based on measurement mode
        if self.config.cluster_mode == MeasurementMode.re_analyse:
            # In re-analysis mode, measurements are not needed, so no hardware setup is performed
            logger.info(
                "Cluster will not be defined as there is no need to take a measurement in re-analysis mode."
            )
        else:
            # In measurement mode, create the cluster and initialize the instrument coordinator
            self.cluster: "Cluster" = self._create_cluster()
            self.lab_ic: "InstrumentCoordinator" = self._create_instrument_coordinator(
                self.cluster
            )

    def _create_cluster(self) -> "Cluster":
        """
        Creates and initializes a Cluster object to represent the hardware cluster
        based on the given IP address in the configuration.
        """
        cluster: "Cluster"
        if self.config.cluster_mode == MeasurementMode.real:
            # Ensure all previous connections are closed before creating a new cluster instance
            Cluster.close_all()

            try:
                # Create a new cluster instance using the specified cluster name and IP address
                cluster = Cluster(dh.cluster_name, str(self.config.cluster_ip))
            except ConnectionRefusedError:
                msg = "Cluster is disconnected. Maybe it has crushed? Try flick it off and on"
                print("-" * len(msg))
                print(f"{Fore.LIGHTRED_EX}{Style.BRIGHT}{msg}{Style.RESET_ALL}")
                print("-" * len(msg))
                quit()

            print(
                f" \n\u26A0 {Fore.MAGENTA}{Style.BRIGHT}Reseting Cluster at IP *{str(self.config.cluster_ip)[-3:]}{Style.RESET_ALL}\n"
            )
            cluster.reset()  # Reset the cluster to a default state for consistency
            return cluster
        else:
            Cluster.close_all()
            dummy_setup = {str(mod): ClusterType.CLUSTER_QCM_RF for mod in range(1, 16)}
            dummy_setup["16"] = ClusterType.CLUSTER_QRM_RF
            dummy_setup["17"] = ClusterType.CLUSTER_QRM_RF
            cluster = Cluster(dh.cluster_name, dummy_cfg=dummy_setup)
            return cluster

    def _create_instrument_coordinator(
        self, clusters: Union["Cluster", List["Cluster"]]
    ) -> "InstrumentCoordinator":
        """
        Sets up an InstrumentCoordinator to manage communication with the cluster
        and configure its modules with specified attenuation settings.
        """
        lab_ic = InstrumentCoordinator("lab_ic")

        # Ensure clusters is a list, even if a single cluster
        clusters = [clusters] if isinstance(clusters, Cluster) else clusters

        # Configure each cluster in the list and add it to the instrument coordinator
        for cluster in clusters:
            # TODO: Setting the attenuation might not be needed any longer if we decide to use the new hw config
            # Set the attenuation values for the modules
            # TODO: Move module configuration into a helper function to reduce redundancy
            for module in self.cluster.modules:
                try:
                    if module.is_qcm_type and module.is_rf_type:
                        module.out0_att(
                            dh.get_legacy("attenuation_setting")["qubit"]
                        )  # For control lines
                        module.out1_att(
                            dh.get_legacy("attenuation_setting")["coupler"]
                        )  # For flux lines
                    elif module.is_qrm_type and module.is_rf_type:
                        module.out0_att(
                            dh.get_legacy("attenuation_setting")["readout"]
                        )  # For readout lines
                except:
                    pass

            # Add the configured cluster to the instrument coordinator and set a timeout
            lab_ic.add_component(ClusterComponent(cluster))
            lab_ic.timeout(self.config.cluster_timeout)

        return lab_ic

    def get_instrument_coordinator(self):
        """Access the instrument coordinator for use by other classes."""
        return self.lab_ic


class NodeManager:
    """
    Manages the initilazation and inspection of node.
    """

    COUPLER_NODE_NAMES = [
        "coupler_spectroscopy",
        "cz_chevron",
        "cz_optimize_chevron",
        "cz_calibration_ssro",
        "cz_calibration_swap_ssro",
        "cz_dynamic_phase_ssro",
        "cz_dynamic_phase_swap_ssro",
        "reset_chevron",
        "process_tomography_ssro",
        "tqg_randomized_benchmarking_ssro",
        "tqg_randomized_benchmarking_interleaved_ssro",
    ]

    def __init__(
        self, lab_ic: "InstrumentCoordinator", config: "CalibrationConfig"
    ) -> None:
        self.config = config
        self.node_factory = NodeFactory()
        self.lab_ic = lab_ic
        self.transmon_configuration = config.transmon_configuration

    @staticmethod
    def topo_order(target_node: str):
        return filtered_topological_order(target_node)

    def inspect_node(self, node_name: str):
        logger.info(f"Inspecting node {node_name}")

        # Populate initial parameters
        populate_initial_parameters(
            self.transmon_configuration,
            self.config.qubits,
            self.config.couplers,
            REDIS_CONNECTION,
        )

        # Check Redis if node is calibrated
        status: "DataStatus" = self._check_calibration_status_redis(node_name)

        populate_node_parameters(
            node_name,
            status == DataStatus.in_spec,
            self.config.transmon_configuration,
            self.config.qubits,
            self.config.couplers,
            REDIS_CONNECTION,
        )

        # Log status
        if status == DataStatus.in_spec:
            logger.info(
                f" \u2714  {Fore.GREEN}{Style.BRIGHT}Node {node_name} in spec{Style.RESET_ALL}"
            )
        else:
            logger.warning(
                f"\u2691\u2691\u2691 {Fore.RED}{Style.BRIGHT}Calibration required for Node {node_name}{Style.RESET_ALL}"
            )

            # Initialize node and update samplespace
            node = self._initialize_node(node_name)
            logger.info(f"Calibrating node {node.name}")

            # Determine the data path for calibration
            data_path = (
                self.config.data_path
                if self.config.cluster_mode == MeasurementMode.re_analyse
                else create_node_data_path(node)
            )

            # Perform calibration
            node.calibrate(data_path, self.config.cluster_mode)

            # TODO:  develop failure strategies ->
            # if node_calibration_status == DataStatus.out_of_spec:
            #     node_expand()
            #     node_calibration_status = self.calibrate_node(node)

    def _initialize_node(self, node_name: str) -> BaseNode:
        """Initializes a node and updates it with user-defined samplespace if available."""
        node = self.node_factory.create_node(
            node_name, self.config.qubits, couplers=self.config.couplers
        )

        # Update node samplespace
        if node.name in self.config.user_samplespace:
            self.update_to_user_samplespace(node, self.config.user_samplespace)

        # Assign the lab instrument coordinator to the node
        node.lab_instr_coordinator = self.lab_ic

        # Log initialization details
        logger.info(
            f"Initializing parameters for qubits: {self.config.qubits} "
            f"and couplers: {self.config.couplers}"
        )
        return node

    def _check_calibration_status_redis(self, node_name: str) -> DataStatus:
        """Queries Redis for the calibration status of each qubit or coupler associated with the node,
        determining if the node is within or out of specification."""
        elements = (
            self.config.couplers
            if node_name in self.COUPLER_NODE_NAMES
            else self.config.qubits
        )
        for element in elements:
            status = REDIS_CONNECTION.hget(f"cs:{element}", node_name)
            if status == "not_calibrated":
                return DataStatus.out_of_spec
            elif status != "calibrated":
                raise ValueError(f"REDIS error: cannot find cs:{element}", node_name)
        return DataStatus.in_spec

    @staticmethod
    def update_to_user_samplespace(node: BaseNode, user_samplespace: dict) -> None:
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
    def __init__(self, config: CalibrationConfig) -> None:
        self.config = config
        self.hardware_manager = HardwareManager(config=config)
        self.lab_ic = self.hardware_manager.get_instrument_coordinator()
        self.node_manager = NodeManager(self.lab_ic, config=config)
        self.topo_order = self.node_manager.topo_order(self.config.target_node_name)

    def calibrate_system(self):
        logger.info("Starting System Calibration")
        number_of_qubits = len(self.config.qubits)
        draw_arrow_chart(f"Qubits: {number_of_qubits}", self.topo_order)

        # TODO: check if coupler node status throws error after REDISFLUSHALL
        populate_quantities_of_interest(
            self.topo_order,
            self.config.qubits,
            self.config.couplers,
            self.node_manager.node_factory,
            REDIS_CONNECTION,
        )

        for calibration_node in self.topo_order:
            self.node_manager.inspect_node(calibration_node)
            logger.info(f"{calibration_node} node is completed")
