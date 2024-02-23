from qblox_instruments import Cluster
from qblox_instruments import PlugAndPlay


# lokiA_IP = '192.0.2.141'
#
# cluster = Cluster('loki', lokiA_IP)
# cluster.reset()


with PlugAndPlay() as p:
    p.print_devices()
