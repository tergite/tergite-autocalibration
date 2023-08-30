from __future__ import annotations
import math
from qcodes.instrument.channel import InstrumentChannel
from qcodes.instrument.parameter import ManualParameter
from qcodes.utils import validators
from quantify_scheduler.enums import BinMode
from quantify_scheduler.device_under_test.transmon_element import BasicTransmonElement, ClocksFrequencies, DispersiveMeasurement, InstrumentBase, measurement_factories, pulse_factories, pulse_library
from quantify_scheduler.backends.circuit_to_device import OperationCompilationConfig, DeviceCompilationConfig
from quantify_scheduler.helpers.validators import Numbers
from quantify_scheduler.operations.gate_library import Measure
from typing import Literal, Optional, Any

class ExtendedClocksFrequencies(InstrumentChannel):
    def __init__(self, parent: InstrumentBase, name: str, **kwargs: Any) -> None:
        super().__init__(parent=parent, name=name)

        self.readout_1 = ManualParameter(
            name="readout_1",
            instrument=self,
            label="Readout frequency when qubit is at |1>",
            unit="Hz",
            initial_value=kwargs.get("readout_1", math.nan),
            vals=Numbers(min_value=0, max_value=1e12, allow_nan=True),
        )

class R12(InstrumentChannel):
    """
    Submodule containing parameters for performing an R12 operations
    """

    def __init__(self, parent: InstrumentBase, name: str, **kwargs: Any) -> None:
        super().__init__(parent=parent, name=name)
        self.ef_amp180 = ManualParameter(
            name="ef_amp180",
            instrument=self,
            label=r"$\pi-pulse amplitude for 12$",
            initial_value=kwargs.get("ef_amp180", math.nan),
            unit="",
            vals=Numbers(min_value=-10, max_value=10, allow_nan=True),
        )

class Spec(InstrumentChannel):
    """
    Submodule containing parameters for performing qubit spectroscopy measurements
    """
    def __init__(self, parent: InstrumentBase, name: str, **kwargs: Any) -> None:
        super().__init__(parent=parent, name=name)
        self.spec_amp = ManualParameter(
            name="spec_amp",
            instrument=self,
            label=r"amplitude for the qubit spectroscopy pulse",
            initial_value=kwargs.get("spec_amp", math.nan),
            unit="",
            vals=Numbers(min_value=-10, max_value=10, allow_nan=True),
        )

        self.spec_duration = ManualParameter(
            name="spec_duration",
            instrument=self,
            initial_value=kwargs.get("spec_duration", 20e-9),
            unit="s",
            vals=validators.Numbers(min_value=0, max_value=1),
        )


class Measure_RO1(Measure):
    def __init__(
        self,
        *qubits: str,
        acq_index: int | None = None,
        # These are the currently supported acquisition protocols.
        acq_protocol: Optional[
            Literal[
                "SSBIntegrationComplex",
                "Trace",
                "TriggerCount",
                "NumericalWeightedIntegrationComplex",
                "ThresholdedAcquisition",
            ]
        ] = None,
        bin_mode: BinMode | None = None,
    ):
        super().__init__(qubits[0], acq_index=acq_index, bin_mode=bin_mode)
        plot_func = "quantify_scheduler.schedules._visualization.circuit_diagram.meter"
        self.data.update(
            {
                "name": f"Measure_RO1 {', '.join(qubits)}",
                "gate_info": {
                    'unitary': None,
                    'plot_func': plot_func,
                    'tex': r'$\langle0|$',
                    'qubits': list(qubits),
                    'acq_index': acq_index,
                    'acq_protocol': acq_protocol,
                    'bin_mode': bin_mode,
                    'operation_type': 'measure_1',
                },
            }
        )
        self._update()


class ExtendedTransmon(BasicTransmonElement):
    def __init__(self, name: str, **kwargs):

        submodules_to_add = {
            'measure_1': DispersiveMeasurement,
            'r12': R12,
            'spec': Spec,
            'extended_clock_freqs': ExtendedClocksFrequencies,
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
            "backend": "quantify_scheduler.backends"
            ".circuit_to_device.compile_circuit_to_device",
            "elements": self._generate_config(),
            "clocks": {
                f"{self.name}.01": self.clock_freqs.f01(),
                f"{self.name}.12": self.clock_freqs.f12(),
                f"{self.name}.ro": self.clock_freqs.readout(),
                f"{self.name}.ro1": self.extended_clock_freqs.readout_1()
            },
            "edges": {},
        }
        cfg_dict["elements"][f"{self.name}"]["measure_1"] = OperationCompilationConfig(
                    factory_func=measurement_factories.dispersive_measurement,
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
                        # "acq_rotation": self.measure.acq_rotation(),
                        # "acq_threshold": self.measure.acq_threshold(),
                    },
                    gate_info_factory_kwargs=["acq_index", "bin_mode", "acq_protocol"],
                )
        cfg_dict["elements"][f"{self.name}"]["r12"] = OperationCompilationConfig(
                    factory_func=pulse_factories.rxy_drag_pulse,
                    factory_kwargs={
                        "ef_amp180": self.r12.ef_amp180(),
                        # "motzoi": self.rxy.motzoi(),
                        "port": self.ports.microwave(),
                        "clock": f"{self.name}.12",
                        # "duration": self.rxy.duration(),
                    },
                    gate_info_factory_kwargs=["theta", "phi"],
                )

        cfg_dict["elements"][f"{self.name}"]["spec"] = OperationCompilationConfig(
                    factory_func=pulse_factories.rxy_drag_pulse,
                    factory_kwargs={
                        "spec_amp": self.spec.spec_amp(),
                        "spec_duration": self.spec.spec_duration(),
                    },
                    gate_info_factory_kwargs=["theta", "phi"],
                )

        dev_cfg = DeviceCompilationConfig.parse_obj(cfg_dict)

        return dev_cfg
