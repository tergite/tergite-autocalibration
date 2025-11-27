import json
import toml
from qblox_instruments import Cluster
from qblox_instruments.qcodes_drivers.module import Module
from tergite_autocalibration.config.globals import ENV

class IQMixerChannel:

    def __init__(self, module:Module, port:int):
        assert module.is_rf_type, f'{module} has no mixers.'
        self.module = module
        self.port = port
        self.lo_freq = self.rf_freq = None
        if module.is_qcm_type:
            self._lo_commands = [f'out{self.port}_lo_freq', f'out{self.port}_lo_cal']
        elif module.is_qrm_type:
            self._lo_commands = [f'out{self.port}_in{self.port}_lo_freq', f'out{self.port}_in{self.port}_lo_cal']

    def set_lo_freq(self, lo_freq:float):
        self.lo_freq = lo_freq

    def set_rf_freq(self, rf_freq:float):
        self.rf_freq = rf_freq

    def lo_calibration(self):
        if self.lo_freq is None:
            raise AttributeError(f'The lo_freq for the module {self.module} has not been assigned yet.')
        
        getattr(self.module, self._lo_commands[0])(self.lo_freq)
        getattr(self.module, self._lo_commands[1])()
        offset_path0 = getattr(self.module, f'out{self.port}_offset_path0')()
        offset_path1 = getattr(self.module, f'out{self.port}_offset_path1')()
        self.lo_offset = (offset_path0, offset_path1)

    def sideband_calibration(self):
        if self.rf_freq is None:
            raise AttributeError(f'The rf_freq for the module {self.module} has not been assigned yet.')
    
        self.module.disconnect_outputs()
        self.module.sequencer0.connect_sequencer(f"out{self.port}")
        getattr(self.module, self._lo_commands[0])(self.lo_freq)
        print(f"lo_freq={self.lo_freq}, rf_freq={self.rf_freq}")
        nco_freq = self.rf_freq - self.lo_freq
        self.module.sequencer0.nco_freq(nco_freq)
        self.module.sequencer0.sideband_cal()
        gain_ratio = getattr(self.module.sequencer0, f'mixer_corr_gain_ratio')()
        phase_offset_degree = getattr(self.module.sequencer0, f'mixer_corr_phase_offset_degree')()
        self.module.arm_sequencer(0)
        self.module.start_sequencer(0)
        self.sideband_offset = (gain_ratio, phase_offset_degree)
        

class IQMixerCalibration:

    def __init__(self, devices, rf_port:str="mw", cluster_ip=None, cluster_config=None, device_config=None):
        self.devices = devices
        self.rf_port = rf_port
        self.default_clock = "01" if rf_port == "mw" else "ro"
        self.cluster_ip = ENV.cluster_ip if cluster_ip is None else cluster_ip
        Cluster.close_all()
        self.cluster = Cluster('cluster', self.cluster_ip)
        self.parse_cluster_config(cluster_config)
        self.parse_device_config(device_config)
        self.create_rf_channels()

    @property
    def all_clocks(self):
        if self.rf_port == "mw":
            return ["01", "12"]
        elif self.rf_port == "res":
            return ["ro", "ro1", "ro2", "ro_2st_opt", "ro_3st_opt"]

    def parse_cluster_config(self, cluster_config):
        if cluster_config is None:
            self.cluster_config_path = str(ENV.config_dir.absolute()) + '/configs/cluster_config.json'
        else:
            self.cluster_config_path = str(ENV.config_dir.absolute()) + f'/configs/{cluster_config}'

        with open(self.cluster_config_path, 'r') as f:
            self.cluster_config = json.load(f)

        self.create_connectivity()
        self.assign_lo_freqs()

    def create_connectivity(self):
        self.connectivity = dict()
        for pair in self.cluster_config['connectivity']['graph']:
            _, module_name, port_name = pair[0].split(".")
            channel_name = pair[1]
            port = int(port_name.split("_")[-1])
            if self.rf_port in channel_name:
                device = channel_name.split(":")[0]
                if device in self.devices:
                    self.connectivity[device] = (getattr(self.cluster, module_name), port)

    def assign_lo_freqs(self):
        modulation_frequencies = self.cluster_config['hardware_options']['modulation_frequencies']
        self._lo_freqs = dict()
        for device in self.devices:
            self._lo_freqs[device] = float(modulation_frequencies[f'{device}:{self.rf_port}-{device}.{self.default_clock}']['lo_freq'])

    def parse_device_config(self, device_config):
        if device_config is None:
            self.device_config_path = str(ENV.config_dir.absolute()) + '/configs/device_config.toml'
        else:
            self.device_config_path = str(ENV.config_dir.absolute()) + f'/configs/{device_config}'

        self.device_config = toml.load(self.device_config_path)
        self.assign_rf_freqs()

    def assign_rf_freqs(self):
        self._rf_freqs = dict()
        for device in self.devices:
            if self.rf_port == "res":
                rf_freq = self.device_config['device']['resonator'][device]['VNA_frequency']
            elif self.rf_port == "mw":
                rf_freq = self.device_config['device']['qubit'][device]['VNA_f01_frequency']
            self._rf_freqs[device] = float(rf_freq)

    def create_rf_channels(self):
        self.rf_channels = dict()
        for device in self.devices:
            module, port = self.connectivity[device]
            IQchannel = self.rf_channels[device] = IQMixerChannel(module, port)
            IQchannel.set_lo_freq(self._lo_freqs[device])
            IQchannel.set_rf_freq(self._rf_freqs[device])

    def lo_calibration(self):
        for device, channel in self.rf_channels.items():
            print(f'IQ calibration for the {self.rf_port} port of {device}')
            channel.lo_calibration()

    def sideband_calibration(self):
        for device, channel in self.rf_channels.items():
            print(f'Sideband calibration for the {self.rf_port} port of {device}')
            channel.sideband_calibration()

    def export_calibration_parameters(self, overwrite=False, save_to_disk=False):
        """
        Can be overrided by another elegant way
        """
        mc = dict()
        for qubit, channel in self.rf_channels.items():
            for clock in self.all_clocks:
                key = f"{qubit}:{self.rf_port}-{qubit}:{clock}"
                mc[key] = dict()
                mc[key]["dc_offset_i"], mc[key]["dc_offset_q"] = channel.lo_offset
                mc[key]["amp_ratio"], mc[key]["phase_error"] = channel.sideband_offset

        if overwrite:
            # Not recommended
            self.cluster_config["hardware_options"]["mixer_corrections"] = mc
            with open(self.cluster_config_path, 'w') as f:
                json.dump(self.cluster_config, f, indent=4)

        if save_to_disk:
            with open(f'tergite_autocalibration/tools/mixer_calibration/mc_parameters_{self.rf_port}.json', 'w') as f:
                json.dump(mc, f, indent=4)