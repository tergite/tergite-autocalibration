from ipaddress import ip_address, IPv4Address

from tergite_autocalibration.config.settings import CLUSTER_IP
from tergite_autocalibration.scripts.calibration_supervisor import (
    CalibrationSupervisor,
    CalibrationConfig,
)
from tergite_autocalibration.scripts.db_backend_update import update_mss
from tergite_autocalibration.utils.enums import ClusterMode

cluster_mode: "ClusterMode" = ClusterMode.real
parsed_cluster_ip: "IPv4Address" = CLUSTER_IP

config = CalibrationConfig(cluster_mode=cluster_mode, cluster_ip=parsed_cluster_ip)
supervisor = CalibrationSupervisor(config)
supervisor.calibrate_system()
