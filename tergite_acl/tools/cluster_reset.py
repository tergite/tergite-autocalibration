from qblox_instruments import Cluster
from qblox_instruments import PlugAndPlay


# TODO: Refactor to tools

lokiA_IP = '192.0.2.141'

cluster = Cluster('loki', lokiA_IP)
cluster.reboot()


# with PlugAndPlay() as p:
#     p.print_devices()
