from __future__ import annotations
import math
from typing import Any, Literal, Optional

from qcodes.instrument.channel import InstrumentChannel
from qcodes.instrument.parameter import ManualParameter
from qcodes.utils import validators
from quantify_scheduler.backends.circuit_to_device import (
    DeviceCompilationConfig,
    OperationCompilationConfig,
)
from quantify_scheduler.device_under_test.transmon_element import (
    BasicTransmonElement,
    ClocksFrequencies,
    DispersiveMeasurement,
    InstrumentBase,
    measurement_factories,
    pulse_factories,
    pulse_library,
)
from quantify_scheduler.enums import BinMode
from quantify_scheduler.helpers.validators import Numbers
from quantify_scheduler.operations.gate_library import Measure, Rxy


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
        self.readout_2 = ManualParameter(
            name="readout_2",
            instrument=self,
            label="Readout frequency when qubit is at |2>",
            unit="Hz",
            initial_value=kwargs.get("readout_2", math.nan),
            vals=Numbers(min_value=0, max_value=1e12, allow_nan=True),
        )
        self.readout_2state_opt = ManualParameter(
            name="readout_2state_opt",
            instrument=self,
            label="Optimal Readout frequency for discriminating |0>,|1>",
            unit="Hz",
            initial_value=kwargs.get("readout_2state_opt", math.nan),
            vals=Numbers(min_value=0, max_value=1e12, allow_nan=True),
        )

        self.readout_3state_opt = ManualParameter(
            name="readout_3state_opt",
            instrument=self,
            label="Optimal Readout frequency for discriminating |0>,|1>, |2>",
            unit="Hz",
            initial_value=kwargs.get("readout_3state_opt", math.nan),
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
            vals=Numbers(min_value=-1, max_value=1, allow_nan=True),
        )

        self.spec_ampl_optimal = ManualParameter(
            name="spec_ampl_optimal",
            instrument=self,
            label=r"optimal spectroscopy amplitude to be used in coupler anticrossing",
            initial_value=kwargs.get("spec_ampl_optimal", math.nan),
            unit="",
            vals=Numbers(min_value=-1, max_value=1, allow_nan=True),
        )

        self.spec_ampl_12_optimal = ManualParameter(
            name="spec_ampl_12_optimal",
            instrument=self,
            label=r"optimal spectroscopy amplitude to be used in coupler anticrossing",
            initial_value=kwargs.get("spec_amp", math.nan),
            unit="",
            vals=Numbers(min_value=-1, max_value=1, allow_nan=True),
        )

        self.spec_duration = ManualParameter(
            name="spec_duration",
            instrument=self,
            initial_value=kwargs.get("spec_duration", 20e-9),
            unit="s",
            vals=Numbers(min_value=0, max_value=1e-3, allow_nan=True),
        )


class Rxy_12(Rxy):
    """
    A single qubit rotation on the 12 transition.
    """

    def __init__(self, qubit: str, theta: float = 180, phi: float = 0):
        super().__init__(theta=theta, phi=phi, qubit=qubit)
        self.data["name"] = (f"Rxy-12({theta:.8g}, {phi:.8g}, '{qubit}')",)
        self.data["gate_info"]["unitary"] = None  # this is not a Qubit operation
        self.data["gate_info"][
            "operation_type"
        ] = "r12"  # this key is used in compilation!

        self._update()  # Update the Operation's internals

    def __str__(self) -> str:
        qubit = self.data["gate_info"]["qubits"][0]
        return f"{self.__class__.__name__}(qubit='{qubit}')"


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
        plot_func = "quantify_scheduler.calibration_schedules._visualization.circuit_diagram.meter"
        self.data.update(
            {
                "name": f"Measure_RO1 {', '.join(qubits)}",
                "gate_info": {
                    "unitary": None,
                    "plot_func": plot_func,
                    "tex": r"$\langle0|$",
                    "qubits": list(qubits),
                    "acq_index": acq_index,
                    "acq_protocol": acq_protocol,
                    "bin_mode": bin_mode,
                    "operation_type": "measure_1",
                    "acq_channel_override": None,
                },
            }
        )
        self._update()


class Measure_RO2(Measure):
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
        plot_func = "quantify_scheduler.calibration_schedules._visualization.circuit_diagram.meter"
        self.data.update(
            {
                "name": f"Measure_RO2 {', '.join(qubits)}",
                "gate_info": {
                    "unitary": None,
                    "plot_func": plot_func,
                    "tex": r"$\langle0|$",
                    "qubits": list(qubits),
                    "acq_index": acq_index,
                    "acq_protocol": acq_protocol,
                    "bin_mode": bin_mode,
                    "operation_type": "measure_2",
                    "acq_channel_override": None,
                },
            }
        )
        self._update()


class Measure_RO_Opt(Measure):
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
        plot_func = "quantify_scheduler.calibration_schedules._visualization.circuit_diagram.meter"
        self.data.update(
            {
                "name": f"Measure_RO_Opt {', '.join(qubits)}",
                "gate_info": {
                    "unitary": None,
                    "plot_func": plot_func,
                    "tex": r"$\langle opt|$",
                    "qubits": list(qubits),
                    "acq_index": acq_index,
                    "acq_protocol": acq_protocol,
                    "bin_mode": bin_mode,
                    "operation_type": "measure_3state_opt",
                    "acq_channel_override": None,
                },
            }
        )
        self._update()
