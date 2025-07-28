# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Pontus Vikstahl 2024
# (C) Copyright Stefan Hill 2024
# (C) Copyright Martin Ahindura 2023
# (C) Copyright Michele Faucci Giannelli 2024, 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os
from dataclasses import dataclass, field
from ipaddress import IPv4Address
from typing import List, Union, FrozenSet

from colorama import Fore, Style
from colorama import init as colorama_init
from qblox_instruments import Cluster
from qblox_instruments.types import ClusterType
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent
from types import MappingProxyType
from tergite_autocalibration.config.globals import (
    CLUSTER_IP,
    CONFIG,
    ENV,
    REDIS_CONNECTION,
)
from tergite_autocalibration.config.legacy import dh
from tergite_autocalibration.config.package import ConfigurationPackage
from tergite_autocalibration.lib.base.node import BaseNode, CouplerNode
from tergite_autocalibration.lib.utils.graph import filtered_topological_order
from tergite_autocalibration.lib.utils.node_factory import NodeFactory
from tergite_autocalibration.utils.backend.redis_utils import (
    populate_initial_parameters,
    populate_node_parameters,
    populate_quantities_of_interest,
)
from tergite_autocalibration.utils.dto.enums import (
    DataStatus,
    MeasurementMode,
)
from tergite_autocalibration.utils.hardware.spi import SpiDAC
from tergite_autocalibration.utils.io.dataset import create_node_data_path
from tergite_autocalibration.utils.logging import logger

# from tergite_autocalibration.utils.logger.tac_logger import logger
from tergite_autocalibration.utils.logging.visuals import draw_arrow_chart

colorama_init()


@dataclass
class CalibrationConfig:
    """
    Configuration settings for the calibration process.
    """

    cluster_mode: "MeasurementMode" = MeasurementMode.real
    cluster_ip: "IPv4Address" = CLUSTER_IP
    cluster_timeout: int = 222
    qubits: List[str] = field(default_factory=lambda: CONFIG.run.qubits)
    couplers: List[str] = field(default_factory=lambda: CONFIG.run.couplers)
    target_node_name: str = CONFIG.run.target_node
    user_samplespace: dict = field(default_factory=lambda: CONFIG.samplespace())


class HardwareManager:
    """
    Manages hardware setup, including initializing clusters and instrument coordinators.
    """

    def __init__(self, config: "CalibrationConfig") -> None:
        # Store the configuration settings and initialize the instrument coordinator
        self.config = config
        self.lab_ic: InstrumentCoordinator = None

        # Check if hardware setup is necessary based on measurement mode
        if self.config.cluster_mode == MeasurementMode.re_analyse:
            # In re-analysis mode, measurements are not needed, so no hardware setup is performed
            logger.info(
                "Cluster will not be defined as there is no need to take a measurement in re-analysis mode."
            )
        else:
            # In measurement mode, create the cluster and initialize the instrument coordinator
            self.cluster: "Cluster" = self._create_cluster()
            self.lab_ic = self._create_instrument_coordinator(self.cluster)

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
                logger.status("-" * len(msg))
                logger.status(f"{Fore.LIGHTRED_EX}{Style.BRIGHT}{msg}{Style.RESET_ALL}")
                logger.status("-" * len(msg))
                quit()

            logger.status(
                f" \n\u26a0 {Fore.MAGENTA}{Style.BRIGHT}Resetting Cluster at IP *{str(self.config.cluster_ip)[-3:]}{Style.RESET_ALL}\n"
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

        # Load attenuation settings for entire system (possibly across multiple clusters)
        output_attenuation_settings = dh.get_output_attenuations()
        connectivity = MappingProxyType(
            {
                str(n): frozenset(neigh.keys())
                for n, neigh in CONFIG.cluster.connectivity.graph.adj.items()
            }
        )

        # Configure each cluster in the list and add it to the instrument coordinator
        for cluster in clusters:
            _configure_cluster_settings(
                cluster,
                connectivity=connectivity,
                output_attenuation_settings=output_attenuation_settings,
            )

            # Add the configured cluster to the instrument coordinator and set a timeout
            lab_ic.add_component(ClusterComponent(cluster))
            lab_ic.timeout(self.config.cluster_timeout)

        return lab_ic

    def create_spi(self, couplers) -> SpiDAC:
        measurement_mode = self.config.cluster_mode
        return SpiDAC(couplers, measurement_mode)

    def get_instrument_coordinator(self):
        """Access the instrument coordinator for use by other classes."""
        return self.lab_ic


# intermediary function in the call stack in case we want to set other cluster settings
def _configure_cluster_settings(
    cluster: Cluster,
    *,
    connectivity: MappingProxyType[str, FrozenSet[str]],
    output_attenuation_settings: MappingProxyType[str, MappingProxyType[str, int]],
):
    _set_output_attenuations(cluster, connectivity, output_attenuation_settings)


def _set_output_attenuations(cluster, connectivity, settings):
    """
    Sets the output attenuations for modules in the given cluster based on the provided settings.

    This function iterates over couplers, resonators, and qubits, finds the corresponding output
    ports from the connectivity map, and applies attenuation settings to the correct output
    channels (complex_output_0 or complex_output_1) for modules that are part of the cluster.

    Args:
        cluster: Cluster object to configure
        connectivity: A mapping that relates device names (with port suffixes) to their physical port paths.
        settings: A dictionary specifying attenuation values for 'coupler', 'resonator', and 'qubit' devices.
    """
    cluster_modules = cluster.get_connected_modules()
    module_names = frozenset(mod.name for _, mod in cluster_modules.items())

    # read the device configuration (device_config.toml) settings for attenuation
    # entire file, all couplers, all qubits, all resonators
    for device_type, quantify_port_suffix in zip(
        ["coupler", "resonator", "qubit"], [":fl", ":res", ":mw"]
    ):
        for name, att in settings[device_type].items():
            quantify_port = name + quantify_port_suffix

            if quantify_port not in connectivity.keys():
                logger.warning(
                    f"Skipping setting attenuation for '{quantify_port}', as it is "
                    "not in the connectivity graph of the cluster_config.json."
                )
                continue

            ports = connectivity[quantify_port]
            assert len(ports) == 1
            port_str = next(iter(ports))

            # e.g. "cluster.module1.complex_output_0"
            cl, mod, port = tuple(port_str.split(sep="."))

            # inputs can also be specified in the connectivity graph, although such
            # mappings are seldomly used in transmon systems, so just do a simple
            # check here that we are actually configuring an output
            assert "output" in port, (name + quantify_port_suffix, port_str)

            # if the cluster that this qubit is mapped to in the connectivity
            # is not the same as the cluster to be configured, then simply skip
            if cl != cluster.name:
                continue

            # skip if the module is not connected
            if "_".join((cl, mod)) not in module_names:
                continue

            # otherwise, use the dedicated QCoDeS function
            # to set the attenuation
            module_obj = getattr(cluster, mod)

            if port == "complex_output_0":
                module_obj.out0_att(att)
            elif port == "complex_output_1":
                module_obj.out1_att(att)
            else:
                raise KeyError(f"Failed to set attenuation for port: {port_str}")

            logger.debug(f"Applied {att}dB attenuation on {port_str}")


class NodeManager:
    """
    Manages the initialization and inspection of node.
    """

    def __init__(
        self, lab_ic: "InstrumentCoordinator", config: "CalibrationConfig"
    ) -> None:
        self.config = config
        self.node_factory = NodeFactory()
        self.lab_ic = lab_ic
        self.spi_manager: SpiDAC = None

        populate_initial_parameters(
            self.config.qubits,
            self.config.couplers,
            REDIS_CONNECTION,
        )

    @staticmethod
    def topo_order(target_node: str):
        return filtered_topological_order(target_node)

    def inspect_node(self, node_name: str, *, ignore_spec: bool = False):
        logger.info(f"Inspecting node {node_name}")

        populate_quantities_of_interest(
            node_name,
            self.node_factory,
            self.config.qubits,
            self.config.couplers,
            REDIS_CONNECTION,
        )

        # Check Redis if node is calibrated
        if ignore_spec:
            status = DataStatus.out_of_spec
            logger.info(f"Ignoring calibration status for {node_name}")
        else:
            status: "DataStatus" = self._check_calibration_status_redis(node_name)

        populate_node_parameters(
            node_name,
            status == DataStatus.in_spec,
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
                CONFIG.run.log_dir
                if self.config.cluster_mode == MeasurementMode.re_analyse
                else create_node_data_path(node.name)
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
            node_name,
            self.config.qubits,
            couplers=self.config.couplers,
        )

        # Update node samplespace
        if node.name in self.config.user_samplespace:
            logger.info(f"Using user_samplespace.py for {node.name}")
            self.update_to_user_samplespace(node, self.config.user_samplespace)

        # Since the node is respomsible for compiling its schedule
        # it needs access to the instrument_coordinator
        node.lab_instr_coordinator = self.lab_ic

        # nodes operating on couplers require access the SPI DACs
        node.spi_manager = self.spi_manager

        # Log initialization details
        logger.info(
            f"Initializing parameters for qubits: {self.config.qubits} "
            f"and couplers: {self.config.couplers}"
        )
        return node

    def _check_calibration_status_redis(self, node_name: str) -> DataStatus:
        """Queries Redis for the calibration status of each qubit or coupler associated with the node,
        determining if the node is within or out of specification."""
        node = self.node_factory.get_node_class(node_name)
        elements = (
            self.config.couplers
            if issubclass(node, CouplerNode)
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

    def calibrate_system(self, node_name: str | None = None, ignore_spec: bool = False):
        logger.info("Starting System Calibration")
        number_of_qubits = len(self.config.qubits)

        calibration_nodes = self.topo_order if node_name is None else [node_name]
        draw_arrow_chart(f"Qubits: {number_of_qubits}", calibration_nodes)

        # The node manager provides every node with access to the DACS
        self.node_manager.spi_manager = self.hardware_manager.create_spi(
            self.config.couplers
        )
        self.node_manager.spi_manager.set_parking_currents(self.config.couplers)

        # Create a copy of the configuration inside the log directory
        # This is to be able to replicate errors caused by configuration
        ConfigurationPackage.from_toml(
            os.path.join(ENV.config_dir, "configuration.meta.toml")
        ).copy(str(CONFIG.run.log_dir))

        for calibration_node in calibration_nodes:
            self.node_manager.inspect_node(calibration_node, ignore_spec=ignore_spec)
            logger.info(f"{calibration_node} node is completed")

    def rerun_analysis(self):
        """
        Reruns the analysis of the target node.
        """

        logger.info("Rerun analysis")
        self.node_manager.inspect_node(self.config.target_node_name)
        logger.info(f"{self.config.target_node_name} node is completed")
