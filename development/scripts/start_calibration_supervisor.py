from ipaddress import IPv4Address

from tergite_autocalibration.config.settings import CLUSTER_IP
from tergite_autocalibration.scripts.calibration_supervisor import CalibrationSupervisor
from tergite_autocalibration.utils.dto.enums import MeasurementMode

cluster_mode: "MeasurementMode" = MeasurementMode.real
parsed_cluster_ip: "IPv4Address" = CLUSTER_IP
supervisor = CalibrationSupervisor(
    cluster_mode=cluster_mode, cluster_ip=parsed_cluster_ip
)
supervisor.calibrate_system()