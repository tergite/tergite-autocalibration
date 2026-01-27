# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs AB 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


import json
from typing import List, TYPE_CHECKING

import toml
from qblox_instruments import Cluster

from tergite_autocalibration.config.globals import (
    CONFIG,
    ENV,
    REDIS_CONNECTION,
    logger,
    CONFIGURATION_PACKAGE,
)
from tergite_autocalibration.tools.mixer_calibration.utils import (
    replace_mixer_corrected_values,
)

if TYPE_CHECKING:
    from qblox_instruments.qcodes_drivers.module import Module


class IQMixerChannel:

    def __init__(self, module: "Module", port: int):
        assert module.is_rf_type, f"{module} has no mixers."
        self.module = module
        self.port = port
        self.lo_freq = self.rf_freq = None
        if module.is_qcm_type:
            self._lo_commands = [f"out{self.port}_lo_freq", f"out{self.port}_lo_cal"]
        elif module.is_qrm_type:
            self._lo_commands = [
                f"out{self.port}_in{self.port}_lo_freq",
                f"out{self.port}_in{self.port}_lo_cal",
            ]

        # Initialize offsets with default values
        self.lo_offset = (0, 0)
        self.sideband_offset = (1, 0)

    def set_lo_freq(self, lo_freq: float):
        self.lo_freq = lo_freq

    def set_rf_freq(self, rf_freq: float):
        self.rf_freq = rf_freq

    def calibrate_lo(self):
        if self.lo_freq is None:
            raise AttributeError(
                f"The lo_freq for the module {self.module} has not been assigned yet."
            )

        getattr(self.module, self._lo_commands[0])(self.lo_freq)
        getattr(self.module, self._lo_commands[1])()
        offset_path0 = 1e-3 * getattr(self.module, f"out{self.port}_offset_path0")()
        offset_path1 = 1e-3 * getattr(self.module, f"out{self.port}_offset_path1")()
        self.lo_offset = (offset_path0, offset_path1)

    def calibrate_sideband(self):
        if self.rf_freq is None:
            raise AttributeError(
                f"The rf_freq for the module {self.module} has not been assigned yet."
            )

        self.module.disconnect_outputs()
        self.module.sequencer0.connect_sequencer(f"out{self.port}")
        getattr(self.module, self._lo_commands[0])(self.lo_freq)
        logger.status(f"lo_freq={self.lo_freq}, rf_freq={self.rf_freq}")
        nco_freq = self.rf_freq - self.lo_freq
        self.module.sequencer0.nco_freq(nco_freq)
        self.module.sequencer0.sideband_cal()
        gain_ratio = self.module.sequencer0.mixer_corr_gain_ratio()
        phase_offset_degree = self.module.sequencer0.mixer_corr_phase_offset_degree()
        self.module.arm_sequencer(0)
        self.module.start_sequencer(0)
        self.sideband_offset = (gain_ratio, phase_offset_degree)


class IQMixerCalibration:

    def __init__(
        self,
        devices: List[str],
        rf_port: str = "mw",
        cluster_ip=None,
        cluster_config=None,
        device_config=None,
    ):
        self.devices = devices
        self.rf_port = rf_port

        # Connect to the cluster
        self.cluster_ip = ENV.cluster_ip if cluster_ip is None else cluster_ip
        Cluster.close_all()
        self.cluster = Cluster("cluster", self.cluster_ip)

        # Load cluster config
        self.cluster_config_path = (
            CONFIGURATION_PACKAGE.config_files["cluster_config"]
            if cluster_config is None
            else cluster_config
        )
        with open(self.cluster_config_path, "r") as f_:
            self.cluster_config = json.load(f_)

        # Load device config
        self.device_config_path = (
            CONFIG.device.filepath if device_config is None else device_config
        )
        self.device_config = toml.load(self.device_config_path)

        # Basic initialization sequence
        self.connectivity = self._init_connectivity()
        self._lo_freqs = self._init_lo_freqs()
        self._rf_freqs = self._init_rf_freqs()
        self.rf_channels = self._init_rf_channels()

    @property
    def all_clocks(self):
        """
        First clock should be default clock, see default_clock property below.
        """
        if self.rf_port == "mw":
            return ["01", "12"]
        elif self.rf_port == "res":
            return ["ro", "ro1", "ro2", "ro_2st_opt", "ro_3st_opt"]
        elif self.rf_port == "fl":
            return ["cz"]

    @property
    def default_clock(self):
        return self.all_clocks[0]

    def _init_connectivity(self):
        connectivity_ = dict()
        for pair in self.cluster_config["connectivity"]["graph"]:
            _, module_name, port_name = pair[0].split(".")
            channel_name = pair[1]
            port = int(port_name.split("_")[-1])
            if self.rf_port in channel_name:
                device = channel_name.split(":")[0]
                if device in self.devices:
                    connectivity_[device] = (
                        getattr(self.cluster, module_name),
                        port,
                    )
        return connectivity_

    def _init_lo_freqs(self):
        lo_freqs_ = dict()
        modulation_frequencies = self.cluster_config["hardware_options"][
            "modulation_frequencies"
        ]
        for device in self.devices:
            lo_freqs_[device] = float(
                modulation_frequencies[
                    f"{device}:{self.rf_port}-{device}.{self.default_clock}"
                ]["lo_freq"]
            )
        return lo_freqs_

    def _init_rf_freqs(self):
        rf_freqs_ = dict()
        for device in self.devices:
            if self.rf_port == "res":
                rf_freq = self.device_config["device"]["resonator"][device][
                    "VNA_frequency"
                ]
            elif self.rf_port == "mw":
                rf_freq = self.device_config["device"]["qubit"][device][
                    "VNA_f01_frequency"
                ]
            elif self.rf_port == "fl":
                cz_pulse_frequency = float(
                    REDIS_CONNECTION.hget(f"couplers:{device}", "cz_pulse_frequency")
                )
                if cz_pulse_frequency is None:
                    raise AttributeError(
                        f"The cz_pulse_frequency of coupler {device} isn't determined yet."
                    )
                else:
                    rf_freq = 4.4e9 - cz_pulse_frequency
            else:
                raise ValueError(f"Unknown rf_port value: {self.rf_port}")

            rf_freqs_[device] = float(rf_freq)
        return rf_freqs_

    def _init_rf_channels(self):
        rf_channels_ = dict()
        for device in self.devices:
            module, port = self.connectivity[device]
            iq_channel = rf_channels_[device] = IQMixerChannel(module, port)
            iq_channel.set_lo_freq(self._lo_freqs[device])
            iq_channel.set_rf_freq(self._rf_freqs[device])
        return rf_channels_

    def calibrate_lo(self):
        for device, channel in self.rf_channels.items():
            logger.status(f"IQ calibration for the {self.rf_port} port of {device}")
            channel.calibrate_lo()

    def calibrate_sideband(self):
        for device, channel in self.rf_channels.items():
            logger.status(
                f"Sideband calibration for the {self.rf_port} port of {device}"
            )
            channel.calibrate_sideband()

    def export_calibration_parameters(self, overwrite=False, save_to_disk=False):
        mc_ = dict()
        for qubit, channel in self.rf_channels.items():
            for clock in self.all_clocks:
                key = f"{qubit}:{self.rf_port}-{qubit}.{clock}"
                mc_[key] = dict()
                mc_[key]["dc_offset_i"], mc_[key]["dc_offset_q"] = channel.lo_offset
                mc_[key]["amp_ratio"], mc_[key]["phase_error"] = channel.sideband_offset

        if overwrite:
            # Not recommended
            replace_mixer_corrected_values(self.cluster_config, mc_)
            with open(self.cluster_config_path, "w") as f_:
                json.dump(self.cluster_config, f_, indent=4)  # type: ignore

        if save_to_disk:
            path = f"tergite_autocalibration/tools/mixer_calibration/mc_parameters_{self.rf_port}.json"
            logger.status(f"Saving calibration for the {self.rf_port} port at {path}")
            with open(path, "w") as f_:
                json.dump(mc_, f_, indent=4)  # type: ignore
