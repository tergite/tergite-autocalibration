# This code is part of Tergite
import argparse

import toml
from colorama import Fore
from colorama import Style
from colorama import init as colorama_init
from qblox_instruments import Cluster
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent

from tergite_acl.config import settings
from tergite_acl.config.settings import CLUSTER_IP, REDIS_CONNECTION
from tergite_acl.lib.node_base import BaseNode
from tergite_acl.lib.nodes.graph import filtered_topological_order
from tergite_acl.lib.node_factory import NodeFactory
from tergite_acl.utils.logger.tac_logger import logger
from tergite_acl.utils.status import MeasurementMode
from tergite_acl.utils.status import DataStatus
from tergite_acl.utils.user_input import user_requested_calibration
from tergite_acl.utils.visuals import draw_arrow_chart
from tergite_acl.utils.dataset_utils import create_node_data_path
from tergite_acl.utils.hardware_utils import SpiDAC, set_qubit_attenuation
from tergite_acl.functions.node_supervisor import monitor_node_calibration
from tergite_acl.utils.redis_utils import populate_initial_parameters, populate_node_parameters, \
    populate_quantities_of_interest

from tergite_acl.utils.dummy_setup import dummy_setup

colorama_init()

def update_to_user_samplespace(node: BaseNode, user_samplespace: dict):
    node_user_samplespace = user_samplespace[node.name]
    for settable, element_samplespace in node_user_samplespace.items():
        if settable in node.schedule_samplespace:
            node.schedule_samplespace[settable] = element_samplespace
        elif settable in node.external_samplespace:
            node.external_samplespace[settable] = element_samplespace
        else:
            raise KeyError(f'{settable} not in any samplespace')
    return

class CalibrationSupervisor():
    def __init__(self, measurement_mode) -> None:
        # Initialize the node factory
        self.node_factory = NodeFactory()
        # TODO: user configuration could be a toml file
        self.qubits = user_requested_calibration['all_qubits']
        self.couplers = user_requested_calibration['couplers']
        self.target_node = user_requested_calibration['target_node']
        self.user_samplespace = user_requested_calibration['user_samplespace']
        # Settings
        self.transmon_configuration = toml.load(settings.DEVICE_CONFIG)
        # TODO: how is the dummy cluster initalized?
        self.measurement_mode = measurement_mode
        self.topo_order = filtered_topological_order(self.target_node)
        self.available_clusters = ['clusterA']
        # TODO: maybe it makes sense to move that part to some hardware utils
        self.available_clusters_dict: dict[str, Cluster] = {}
        self.lab_ic = self.create_lab_ic()
        if self.target_node == 'cz_chevron':
            self.dacs = {}
            self.spi = SpiDAC()
            for coupler in self.couplers:
                self.dacs[coupler] = self.spi.create_spi_dac(coupler)
        logger.info('Initialized Calibration Supervisor')

    def create_lab_ic(self):
        Cluster.close_all()
        for cluster_name in self.available_clusters:
            if self.measurement_mode == MeasurementMode.real:
                cluster = Cluster(cluster_name, str(CLUSTER_IP))
                logger.info('Reseting Cluster')
                cluster.reset()
            elif self.measurement_mode == MeasurementMode.dummy:
                cluster = Cluster(cluster_name, dummy_cfg=dummy_setup)
            else:
                raise ValueError('Undefined Cluster Status')

            self.available_clusters_dict[cluster_name] = cluster

        ###############
        ### set attenuation
        ###############
        print('WARNING SETTING ATTENUATION')
        for qubit in self.qubits:
            att_in_db = 8
            cluster = self.available_clusters_dict['clusterA']
            set_qubit_attenuation(cluster, qubit, att_in_db)

        # set_module_att(clusterA)
        ic = InstrumentCoordinator('lab_ic')
        for cluster in self.available_clusters_dict.values():
            ic.add_component(ClusterComponent(cluster))
        ic.timeout(222)
        return ic


    def calibrate_system(self):
        # TODO: everything which is not in the inspect or calibrate function should go here
        logger.info('Starting System Calibration')
        number_of_qubits = len(self.qubits)
        draw_arrow_chart(f'Qubits: {number_of_qubits}', self.topo_order)

        populate_quantities_of_interest(
            self.transmon_configuration,
            self.qubits,
            self.couplers,
            REDIS_CONNECTION
        )

        for calibration_node in self.topo_order:
            self.inspect_node(calibration_node)
            logger.info(f'{calibration_node} node is completed')


    def inspect_node(self, node_name: str):
        # TODO: the inspect node function could be part of the node
        logger.info(f'Inspecting node {node_name}')

        node: BaseNode = self.node_factory.create_node(
            node_name, self.qubits, couplers=self.couplers
        )

        if node.name in self.user_samplespace:
            update_to_user_samplespace(node, self.user_samplespace)

        # some nodes e.g. cw spectroscopy needs access to the instruments
        node.lab_instr_coordinator = self.available_clusters_dict

        populate_initial_parameters(
            self.transmon_configuration,
            self.qubits,
            self.couplers,
            REDIS_CONNECTION
        )

        if node_name in ['coupler_spectroscopy', 'cz_chevron']:
            coupler_statuses = [REDIS_CONNECTION.hget(f"cs:{coupler}", node_name) == 'calibrated' for coupler in self.couplers]
            #node is calibrated only when all couplers have the node calibrated:
            is_node_calibrated = all(coupler_statuses)
        else:
            qubits_statuses = [REDIS_CONNECTION.hget(f"cs:{qubit}", node_name) == 'calibrated' for qubit in self.qubits]
            #node is calibrated only when all qubits have the node calibrated:
            is_node_calibrated = all(qubits_statuses)

        populate_node_parameters(
            node_name,
            is_node_calibrated,
            self.transmon_configuration,
            self.qubits,
            self.couplers,
            REDIS_CONNECTION
        )

        #Check Redis if node is calibrated
        status = DataStatus.undefined

        if node_name in ['coupler_spectroscopy', 'cz_chevron', 'cz_optimize_chevron']:
            for coupler in self.couplers:
                # the calibrated, not_calibrated flags may be not necessary,
                # just store the DataStatus on Redis
                is_Calibrated = REDIS_CONNECTION.hget(f"cs:{coupler}", node_name)
                if is_Calibrated == 'not_calibrated':
                    status = DataStatus.out_of_spec
                    break  # even if a single qubit is not_calibrated mark as out_of_spec
                elif is_Calibrated == 'calibrated':
                    status = DataStatus.in_spec
                else:
                    raise ValueError(f'status: {status}')
        else:
            for qubit in self.qubits:
                # the calibrated, not_calibrated flags may be not necessary,
                # just store the DataStatus on Redis
                is_Calibrated = REDIS_CONNECTION.hget(f"cs:{qubit}", node_name)
                if is_Calibrated == 'not_calibrated':
                    status = DataStatus.out_of_spec
                    break  # even if a single qubit is not_calibrated mark as out_of_spec
                elif is_Calibrated == 'calibrated':
                    status = DataStatus.in_spec
                else:
                    raise ValueError(f'status: {status}')



        if status == DataStatus.in_spec:

            print(f' \u2714  {Fore.GREEN}{Style.BRIGHT}Node {node_name} in spec{Style.RESET_ALL}')
            # print(f'{Fore.GREEN}{Style.BRIGHT} + u" \u2714 " + Node {node} in spec{Style.RESET_ALL}')
            return

        elif status == DataStatus.out_of_spec:
            print(u'\u2691\u2691\u2691 ' + f'{Fore.RED}{Style.BRIGHT}Calibration required for Node {node_name}{Style.RESET_ALL}')
            node_calibration_status = self.calibrate_node(node)

            #TODO : develop failure strategies ->
            # if node_calibration_status == DataStatus.out_of_spec:
            #     node_expand()
            #     node_calibration_status = self.calibrate_node(node)


    def calibrate_node(self, node) -> DataStatus:
        logger.info(f'Calibrating node {node.name}')
        # TODO: This should be in the node initializer
        data_path = create_node_data_path(node)
        # TODO: This should be the refactored such that the node can be run like node.calibrate()
        monitor_node_calibration(node, data_path, self.lab_ic, self.measurement_mode)

        return


# main
if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='Tergite Automatic Calibration',)
    parser.add_argument(
        '--d', dest='measurement_mode',
        action='store_const',
        const=MeasurementMode.dummy, default=MeasurementMode.real
    )
    args = parser.parse_args()


    supervisor = CalibrationSupervisor(args.measurement_mode)
    supervisor.calibrate_system()

    # if target_node == 'cz_chevron':
    #     set_module_att(clusterA)
    #     for coupler in couplers:
    #         spi = SpiDAC()
    #         spi.set_parking_current(coupler)

