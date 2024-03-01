import argparse
from qblox_instruments import Cluster
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent
import toml
from tergite_acl.lib.nodes import filtered_topological_order
from tergite_acl.utils.status import ClusterStatus
from tergite_acl.workers.hardware_utils import set_module_att
import numpy as np
from tergite_acl.utils.user_input import user_requested_calibration
from workers.linear_calibration_supervisor import calibrate_topo_sorted_path
from tergite_acl.config.settings import CLUSTER_IP

parking_currents = np.linspace(-1e-3, 1e-3, 5)

def nullify_nodes_on_path(node_name: str):
    pass

parser = argparse.ArgumentParser(prog='Tergite Automatic Calibration',)
parser.add_argument(
    '--d', dest='cluster_status',
    action='store_const',
    const=ClusterStatus.dummy, default=ClusterStatus.real
)
args = parser.parse_args()
# Settings
transmon_configuration = toml.load('./config/device_config.toml')


qubits = user_requested_calibration['all_qubits']
couplers = user_requested_calibration['couplers']
target_node = user_requested_calibration['target_node']

if args.cluster_status == ClusterStatus.real:
    Cluster.close_all()
    clusterA = Cluster("clusterA", CLUSTER_IP)
    # set_module_att(clusterA)
    lab_ic = InstrumentCoordinator('lab_ic')
    lab_ic.add_component(ClusterComponent(clusterA))
    lab_ic.timeout(222)

set_module_att(clusterA)

topo_order = filtered_topological_order(target_node)
calibrate_topo_sorted_path(topo_order)


# for current in parking_currents:
#     for coupler in couplers:
#         spi = SpiDAC()
#         spi.set_parking_current(coupler)
#
#     target_node = 'cz_chevron'
#
#     nullify_nodes_on_path(target_node)
#
#     topo_order = filtered_topological_order(target_node)
#     calibrate_topo_sorted_path(topo_order)

