import math
from typing import Dict, Any

from qcodes.instrument import InstrumentChannel
from qcodes.instrument.base import InstrumentBase
from qcodes.instrument.parameter import ManualParameter

from quantify_scheduler.backends.graph_compilation import OperationCompilationConfig
from quantify_scheduler.device_under_test.transmon_element import pulse_factories
from quantify_scheduler.helpers.validators import Numbers
from quantify_scheduler.device_under_test.edge import Edge
# from quantify_scheduler.operations.pulse_factories import composite_square_pulse
from quantify_scheduler.resources import BasebandClockResource
from tergite_autocalibration.utils.extended_pulse_factories import composite_soft_square_pulse


class Spec(InstrumentChannel):
    """
    Submodule containing parameters for performing qubit spectroscopy measurements
    """
    def __init__(self, parent: InstrumentBase, name: str, **kwargs: Any) -> None:
        super().__init__(parent=parent, name=name)
        self.spec_amp = ManualParameter(
            name="coupler_spec_amp",
            instrument=self,
            label=r"amplitude for the coupler spectroscopy pulse",
            initial_value=kwargs.get("coupler_spec_amp", math.nan),
            unit="",
            vals=Numbers(min_value=-10, max_value=10, allow_nan=True),
        )


class CZ(InstrumentChannel):
    """
    Submodule containing parameters for performing a CZ operation
    """

    def __init__(self, parent: InstrumentBase, name: str, **kwargs: Any) -> None:
        super().__init__(parent=parent, name=name)
        self.square_amp = ManualParameter(
            "square_amp",
            docstring=r"""Amplitude of the square envelope.""",
            unit="V",
            initial_value=0.1,
            vals=Numbers(min_value=0, max_value=1e12, allow_nan=True),
            instrument=self,
        )

        self.square_duration = ManualParameter(
            "square_duration",
            docstring=r"""The square pulse duration in seconds.""",
            unit="s",
            initial_value=200e-9,
            vals=Numbers(min_value=0, max_value=1e12, allow_nan=True),
            instrument=self,
        )

        self.cz_width = ManualParameter(
            name="cz_width",
            docstring=r"""AC flux pulse rising and lowering edge width""",
            instrument=self,
            initial_value=4e-9,
            unit="s",
            vals=Numbers(min_value=0, max_value=1e12, allow_nan=True),
        )

        self.parent_phase_correction = ManualParameter(
            name="parent_phase_correction",
            docstring=r"""The phase correction for the parent qubit after the"""
            r""" square pulse operation has been performed.""",
            unit="degrees",
            initial_value=0,
            vals=Numbers(min_value=-1e12, max_value=1e12, allow_nan=True),
        )

        self.child_phase_correction = ManualParameter(
            name="child_phase_correction",
            docstring=r"""The phase correction for the parent qubit after the"""
            r""" square pulse operation has been performed.""",
            unit="degrees",
            initial_value=0,
            vals=Numbers(min_value=-1e12, max_value=1e12, allow_nan=True),
        )

        # self.add_parameter(
        #     name=f"parent_phase_correction",
        #     docstring=r"""The phase correction for the parent qubit after the"""
        #     r""" square pulse operation has been performed.""",
        #     unit="degrees",
        #     parameter_class=ManualParameter,
        #     initial_value=0,
        #     vals=Numbers(min_value=-1e12, max_value=1e12, allow_nan=True),
        # )

        # self.add_parameter(
        #     name=f"child_phase_correction",
        #     docstring=r"""The phase correction for the child qubit after the"""
        #     r""" Square pulse operation has been performed.""",
        #     unit="degrees",
        #     parameter_class=ManualParameter,
        #     initial_value=0,
        #     vals=Numbers(min_value=-1e12, max_value=1e12, allow_nan=True),
        # )

        self.dc_flux = ManualParameter(
            name="dc_flux",
            instrument=self,
            docstring=r"""DC flux for coupler parking position""",
            initial_value=0,
            unit="A",
            vals=Numbers(min_value=-3e-3, max_value=3e-3, allow_nan=True),
        )

        self.dc_flux_0 = ManualParameter(
            name="dc_flux_0",
            instrument=self,
            docstring=r"""DC flux quanta for the coupler tunability""",
            initial_value=0,
            unit="A",
            vals=Numbers(min_value=-3e-3, max_value=3e-3, allow_nan=True),
        )

        self.dc_flux_offset = ManualParameter(
            name="dc_flux_offset",
            instrument=self,
            label=r"DC flux offset for the coupler tunability",
            initial_value=0,
            unit="A",
            vals=Numbers(min_value=-3e-3, max_value=3e-3, allow_nan=True),
        )

        self.edge_group = ManualParameter(
            name="edge_group",
            instrument=self,
            label=r"Group assignment for the edge",
            initial_value=0,
            unit="",
            vals=Numbers(min_value=-10, max_value=10, allow_nan=True),
        )

class EdgeClocksFrequencies(InstrumentChannel):
    def __init__(self, parent: InstrumentBase, name: str, **kwargs: Any) -> None:
        super().__init__(parent=parent, name=name)

        self.cz_freq = ManualParameter(
            name="cz_freq",
            docstring=r"""AC flux frequency for a CZ gate""",
            instrument=self,
            unit="Hz",
            initial_value=100e6,
            vals=Numbers(min_value=0, max_value=1e12, allow_nan=True),
        )

class CompositeSquareEdge(Edge):
    """
    An example Edge implementation which connects two BasicTransmonElements within a
    QuantumDevice. This edge implements a square flux pulse and two virtual z
    phase corrections for the CZ operation between the two BasicTransmonElements.
    """

    def __init__(
        self,
        parent_element_name: str,
        child_element_name: str,
        **kwargs,
    ):
        super().__init__(
            parent_element_name=parent_element_name,
            child_element_name=child_element_name,
            **kwargs,
        )

        self.add_submodule("cz", CZ(self, "cz"))
        self.add_submodule("spec", Spec(self, "spec"))
        self.add_submodule('clock_freqs', EdgeClocksFrequencies(self, "clock_freqs"))

    def generate_edge_config(self) -> Dict[str, Dict[str, OperationCompilationConfig]]:
        """
        Fills in the edges information to produce a valid device config for the
        quantify-scheduler making use of the
        :func:`~.circuit_to_device._compile_circuit_to_device` function.
        """
        # pylint: disable=line-too-long
        edge_op_config = {
            f"{self.name}": {
                "CZ": OperationCompilationConfig(
                    factory_func=composite_soft_square_pulse,
                    factory_kwargs={
                        "square_port": self.name+":fl",
                        "square_clock": self.name+".cz",
                        "square_amp": self.cz.square_amp(),
                        "square_duration": self.cz.square_duration(),
                        "virt_z_parent_qubit_phase": self.cz.parent_phase_correction(),
                        "virt_z_parent_qubit_clock": f"{self.parent_device_element.name}.01",
                        "virt_z_child_qubit_phase": self.cz.child_phase_correction(),
                        "virt_z_child_qubit_clock": f"{self.child_device_element.name}.01",
                    },
                ),
                "spec": OperationCompilationConfig(
                    factory_func=pulse_factories.rxy_drag_pulse,
                    factory_kwargs={
                        'coupler_spec_amp': self.spec.coupler_spec_amp(),
                    },
                    gate_info_factory_kwargs=['theta', 'phi'],
                )
            }
        }

        return edge_op_config
