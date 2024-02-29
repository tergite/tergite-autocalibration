from tergite_acl.utils.root_path import project_root
# from config.LO_hw_config import hardware_config
# hw_config_json = project_root / 'config/HARDWARE_CONFIGURATION_LOKIA_20231120.json'
# hw_config_json = project_root / 'config/HARDWARE_CONFIGURATION_LOKIA_COUPLERS.json'
hw_config_json = project_root / 'config/HARDWARE_CONFIGURATION_LOKIB_25092023.json'

device_config_file = project_root / 'config/device_config.toml'

lokiA_IP = '192.0.2.141'

spiA_serial_port = '/dev/ttyACM0'
