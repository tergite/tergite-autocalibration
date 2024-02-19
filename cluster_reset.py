from qblox_instruments import Cluster

lokiA_IP = '192.0.2.141'

cluster = Cluster('loki', lokiA_IP)
cluster.reset()
