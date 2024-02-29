# This code is part of Tergite
import argparse

from tergite_acl.utilities.status import DataStatus
from tergite_acl.logger.tac_logger import logger
from tergite_acl.nodes.node import NodeFactory
from tergite_acl.utilities.status import ClusterStatus
from qblox_instruments import Cluster
from tergite_acl.workers.hardware_utils import SpiDAC
from tergite_acl.workers.dataset_utils import create_node_data_path

from tergite_acl.nodes.graph import filtered_topological_order
from tergite_acl.utilities.visuals import draw_arrow_chart
from tergite_acl.config_files.settings import lokiA_IP, device_config_file
# from workers.dummy_setup import dummy_cluster

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
from tergite_acl.utilities.user_input import user_requested_calibration
import toml
import redis
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent
from tergite_acl.workers.monitor_worker import monitor_node_calibration
from tergite_acl.workers.redis_utils import populate_initial_parameters, populate_node_parameters, populate_quantities_of_interest

colorama_init()


class CalibrationSupervisor():
    def __init__(self) -> None:
        # Initialize the node factory
        self.node_factory = NodeFactory()
        # TODO: redis connection could be imported once globally
        self.redis_connection = redis.Redis(decode_responses=True)
        # TODO: user configuration could be a toml file
        self.qubits = user_requested_calibration['all_qubits']
        self.couplers = user_requested_calibration['couplers']
        self.target_node = user_requested_calibration['target_node']
        # Settings
        # TODO: move to .env file
        self.transmon_configuration = toml.load('/home/calibration/repos/tergite-autocalibration-lite/tergite_acl/config_files/device_config.toml')
        # TODO: how is the dummy cluster initalized?
        self.cluster_status = ClusterStatus.real
        self.topo_order = filtered_topological_order(self.target_node)
        # TODO: maybe it makes sense to move that part to some hardware utils
        self.lab_ic = self.create_lab_ic()
        if self.target_node == 'cz_chevron':
            self.dacs = {}
            self.spi = SpiDAC()
            for coupler in self.couplers:
                self.dacs[coupler] = self.spi.create_spi_dac(coupler)

    def create_lab_ic(self):
        # TODO: maybe this could be move to some lab utils
        # TODO: the args variable is not global
        if args.cluster_status == ClusterStatus.real:
            Cluster.close_all()
            clusterA = Cluster("clusterA", lokiA_IP)
            # set_module_att(clusterA)
            ic = InstrumentCoordinator('lab_ic')
            ic.add_component(ClusterComponent(clusterA))
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
            self.redis_connection
        )

        for calibration_node in self.topo_order:
            self.inspect_node(calibration_node)
            logger.info(f'{calibration_node} node is completed')


    def inspect_node(self, node_name: str):
        # TODO: the inspect node function could be part of the node
        logger.info(f'Inspecting node {node_name}')

        node = self.node_factory.create_node(
            node_name, self.qubits, couplers=self.couplers
        )

        redis_connection = self.redis_connection

        populate_initial_parameters(
            self.transmon_configuration,
            self.qubits,
            self.couplers,
            self.redis_connection
        )

        if node_name in ['coupler_spectroscopy', 'cz_chevron']:
            coupler_statuses = [redis_connection.hget(f"cs:{coupler}", node_name) == 'calibrated' for coupler in self.couplers]
            #node is calibrated only when all couplers have the node calibrated:
            is_node_calibrated = all(coupler_statuses)
        else:
            qubits_statuses = [redis_connection.hget(f"cs:{qubit}", node_name) == 'calibrated' for qubit in self.qubits]
            #node is calibrated only when all qubits have the node calibrated:
            is_node_calibrated = all(qubits_statuses)

        populate_node_parameters(
            node_name,
            is_node_calibrated,
            self.transmon_configuration,
            self.qubits,
            self.couplers,
            self.redis_connection
        )

        #Check Redis if node is calibrated
        status = DataStatus.undefined

        if node_name in ['coupler_spectroscopy', 'cz_chevron', 'cz_optimize_chevron']:
            for coupler in self.couplers:
                # the calibrated, not_calibrated flags may be not necessary,
                # just store the DataStatus on Redis
                is_Calibrated = redis_connection.hget(f"cs:{coupler}", node_name)
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
                is_Calibrated = redis_connection.hget(f"cs:{qubit}", node_name)
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
        monitor_node_calibration(node, data_path, self.lab_ic)

        return


# main
if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='Tergite Automatic Calibration',)
    parser.add_argument(
        '--d', dest='cluster_status',
        action='store_const',
        const=ClusterStatus.dummy, default=ClusterStatus.real
    )
    args = parser.parse_args()

    supervisor = CalibrationSupervisor()
    supervisor.calibrate_system()

    # if target_node == 'cz_chevron':
    #     set_module_att(clusterA)
    #     for coupler in couplers:
    #         spi = SpiDAC()
    #         spi.set_parking_current(coupler)

