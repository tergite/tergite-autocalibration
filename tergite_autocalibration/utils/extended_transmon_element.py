# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from __future__ import annotations

from quantify_scheduler.backends.circuit_to_device import (
    DeviceCompilationConfig,
    OperationCompilationConfig,
)
from quantify_scheduler.device_under_test.transmon_element import (
    BasicTransmonElement,
    DispersiveMeasurement,
    measurement_factories,
    pulse_factories,
    pulse_library,
)

from tergite_autocalibration.utils.extended_gates import (
    R12,
    Spec,
    ExtendedClocksFrequencies,
)


class ExtendedTransmon(BasicTransmonElement):
    def __init__(self, name: str, **kwargs):
        submodules_to_add = {
            "measure_1": DispersiveMeasurement,
            "measure_2": DispersiveMeasurement,
            "measure_3state_opt": DispersiveMeasurement,
            "r12": R12,
            "spec": Spec,
            "extended_clock_freqs": ExtendedClocksFrequencies,
        }
        submodule_data = {
            sub_name: kwargs.pop(sub_name, {}) for sub_name in submodules_to_add.keys()
        }
        super().__init__(name, **kwargs)

        for sub_name, sub_class in submodules_to_add.items():
            self.add_submodule(
                sub_name,
                sub_class(
                    parent=self, name=sub_name, **submodule_data.get(sub_name, {})
                ),
            )

    def generate_device_config(self) -> DeviceCompilationConfig:
        cfg_dict = {
            "elements": self._generate_config(),
            "clocks": {
                f"{self.name}.01": self.clock_freqs.f01(),
                f"{self.name}.12": self.clock_freqs.f12(),
                f"{self.name}.ro": self.clock_freqs.readout(),
                f"{self.name}.ro1": self.extended_clock_freqs.readout_1(),
                f"{self.name}.ro2": self.extended_clock_freqs.readout_2(),
                f"{self.name}.ro_2st_opt": self.extended_clock_freqs.readout_2state_opt(),
                f"{self.name}.ro_3st_opt": self.extended_clock_freqs.readout_3state_opt(),
            },
            "edges": {},
        }
        cfg_dict["elements"][f"{self.name}"]["measure_1"] = OperationCompilationConfig(
            factory_func=measurement_factories.dispersive_measurement_transmon,
            factory_kwargs={
                "port": self.ports.readout(),
                # use different clock: ####
                "clock": f"{self.name}.ro1",
                ############################
                "pulse_type": self.measure.pulse_type(),
                "pulse_amp": self.measure.pulse_amp(),
                "pulse_duration": self.measure.pulse_duration(),
                "acq_delay": self.measure.acq_delay(),
                "acq_duration": self.measure.integration_time(),
                "acq_channel": self.measure.acq_channel(),
                "acq_protocol_default": "SSBIntegrationComplex",
                "reset_clock_phase": self.measure.reset_clock_phase(),
                "reference_magnitude": pulse_library.ReferenceMagnitude.from_parameter(
                    self.measure.reference_magnitude
                ),
                "acq_weights_a": self.measure.acq_weights_a(),
                "acq_weights_b": self.measure.acq_weights_b(),
                "acq_weights_sampling_rate": self.measure.acq_weights_sampling_rate(),
                "acq_rotation": self.measure.acq_rotation(),
                "acq_threshold": self.measure.acq_threshold(),
            },
            gate_info_factory_kwargs=[
                "acq_channel_override",
                "acq_index",
                "bin_mode",
                "acq_protocol",
            ],
        )
        cfg_dict["elements"][f"{self.name}"]["measure_2"] = OperationCompilationConfig(
            factory_func=measurement_factories.dispersive_measurement_transmon,
            factory_kwargs={
                "port": self.ports.readout(),
                # use different clock: ####
                "clock": f"{self.name}.ro2",
                ############################
                "pulse_type": self.measure.pulse_type(),
                "pulse_amp": self.measure.pulse_amp(),
                "pulse_duration": self.measure.pulse_duration(),
                "acq_delay": self.measure.acq_delay(),
                "acq_duration": self.measure.integration_time(),
                "acq_channel": self.measure.acq_channel(),
                # 'acq_channel_override': None,
                "acq_protocol_default": "SSBIntegrationComplex",
                "reset_clock_phase": self.measure.reset_clock_phase(),
                "reference_magnitude": pulse_library.ReferenceMagnitude.from_parameter(
                    self.measure.reference_magnitude
                ),
                "acq_weights_a": self.measure.acq_weights_a(),
                "acq_weights_b": self.measure.acq_weights_b(),
                "acq_weights_sampling_rate": self.measure.acq_weights_sampling_rate(),
                # 'acq_rotation': self.measure.acq_rotation(),
                # 'acq_threshold': self.measure.acq_threshold(),
            },
            gate_info_factory_kwargs=[
                "acq_channel_override",
                "acq_index",
                "bin_mode",
                "acq_protocol",
            ],
        )
        cfg_dict["elements"][f"{self.name}"]["measure_3state_opt"] = (
            OperationCompilationConfig(
                factory_func=measurement_factories.dispersive_measurement_transmon,
                factory_kwargs={
                    "port": self.ports.readout(),
                    # use different clock: ####
                    "clock": f"{self.name}.ro_3st_opt",
                    ############################
                    "pulse_type": self.measure.pulse_type(),
                    "pulse_amp": self.measure.pulse_amp(),
                    "pulse_duration": self.measure.pulse_duration(),
                    "acq_delay": self.measure.acq_delay(),
                    "acq_duration": self.measure.integration_time(),
                    "acq_channel": self.measure.acq_channel(),
                    # 'acq_channel_override': None,
                    "acq_protocol_default": "SSBIntegrationComplex",
                    "reset_clock_phase": self.measure.reset_clock_phase(),
                    "reference_magnitude": pulse_library.ReferenceMagnitude.from_parameter(
                        self.measure.reference_magnitude
                    ),
                    "acq_weights_a": self.measure.acq_weights_a(),
                    "acq_weights_b": self.measure.acq_weights_b(),
                    "acq_weights_sampling_rate": self.measure.acq_weights_sampling_rate(),
                    # 'acq_rotation': self.measure.acq_rotation(),
                    # 'acq_threshold': self.measure.acq_threshold(),
                },
                gate_info_factory_kwargs=[
                    "acq_channel_override",
                    "acq_index",
                    "bin_mode",
                    "acq_protocol",
                ],
            )
        )
        cfg_dict["elements"][f"{self.name}"]["r12"] = OperationCompilationConfig(
            factory_func=pulse_factories.rxy_drag_pulse,
            factory_kwargs={
                "amp180": self.r12.ef_amp180(),
                "motzoi": self.r12.ef_motzoi(),
                "port": self.ports.microwave(),
                "clock": f"{self.name}.12",
                "duration": self.rxy.duration(),
            },
            gate_info_factory_kwargs=["theta", "phi"],
        )

        cfg_dict["elements"][f"{self.name}"]["spec"] = OperationCompilationConfig(
            factory_func=pulse_factories.rxy_drag_pulse,
            factory_kwargs={
                "spec_amp": self.spec.spec_amp(),
                "spec_ampl_optimal": self.spec.spec_ampl_optimal(),
                "spec_ampl_12_optimal": self.spec.spec_ampl_12_optimal(),
                "spec_duration": self.spec.spec_duration(),
            },
            gate_info_factory_kwargs=["theta", "phi"],
        )

        dev_cfg = DeviceCompilationConfig.parse_obj(cfg_dict)

        return dev_cfg
