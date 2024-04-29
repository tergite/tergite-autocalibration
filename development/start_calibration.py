from ipaddress import IPv4Address

from tergite_acl.config.settings import CLUSTER_IP
from tergite_acl.scripts.calibration_supervisor import CalibrationSupervisor


cluster_mode: 'ClusterMode' = ClusterMode.real
parsed_cluster_ip: 'IPv4Address' = CLUSTER_IP

supervisor = CalibrationSupervisor(cluster_mode=cluster_mode,
                                    cluster_ip=parsed_cluster_ip)
supervisor.calibrate_system()