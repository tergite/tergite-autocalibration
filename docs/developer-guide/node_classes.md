# Node classes

The execution of most of the nodes consists of a single schedule compilation, a single measurement and a single
post-processing.
Although for most of the nodes this workflow suffices, there are exceptions while this workflow can become limiting in
more advanced implementations.

To allow greater flexibility in the node implementations the nodes are categorized:

- `ScheduleNode`: The simple way of doing the measurement and having an analysis afterward. This node compiles one time
    - There is only `node.schedule_samplespace` if the sweeping takes place within the schedule.
- `ExternalParameterNode`: A looping over an external parameter during the sweep. This node compiles several times.
    - There are both `node.schedule_samplespace`  and `node.external_samplespace` if there are sweeping parameters
      outside the schedule. For example the `coupler_spectroscopy` node sweeps the `dc_current` outside of the schedule:

Below, there is an example for an `ExternalParameterNode` implementation.

```python
import numpy as np

from tergite_autocalibration.lib.nodes.coupler.spectroscopy.analysis import (
    CouplerSpectroscopyNodeAnalysis,
)

from tergite_autocalibration.lib.nodes.external_parameter_node import (
    ExternalParameterNode,
)

from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.measurement import (
    TwoTonesMultidimMeasurement,
)

from tergite_autocalibration.lib.utils.samplespace import qubit_samples
from tergite_autocalibration.utils.dto.enums import MeasurementMode
from tergite_autocalibration.utils.hardware.spi import SpiDAC


class CouplerSpectroscopyNode(ExternalParameterNode):
    measurement_obj = TwoTonesMultidimMeasurement
    analysis_obj = CouplerSpectroscopyNodeAnalysis
    coupler_qois = ["parking_current", "current_range"]

    def __init__(
            self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.couplers = couplers
        self.qubit_state = 0
        self.schedule_keywords["qubit_state"] = self.qubit_state
        self.coupled_qubits = self.get_coupled_qubits()
        self.coupler = self.couplers[0]

        self.mode = MeasurementMode.real
        self.spi_dac = SpiDAC(self.mode)
        self.dac = self.spi_dac.create_spi_dac(self.coupler)

        self.all_qubits = self.coupled_qubits

        self.schedule_samplespace = {
            "spec_frequencies": {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            }
        }

        self.external_samplespace = {
            "dc_currents": {self.coupler: np.arange(-2.5e-3, 2.5e-4, 280e-6)},
        }

    def get_coupled_qubits(self) -> list:
        if len(self.couplers) > 1:
            print("Multiple couplers, lets work with only one")
        coupled_qubits = self.couplers[0].split(sep="_")
        self.coupler = self.couplers[0]
        return coupled_qubits

    def pre_measurement_operation(self, reduced_ext_space):
        iteration_dict = reduced_ext_space["dc_currents"]
        this_iteration_value = list(iteration_dict.values())[0]
        print(f"{ this_iteration_value = }")
        self.spi_dac.set_dac_current(self.dac, this_iteration_value)

    def final_operation(self):
        print("Final Operation")
        self.spi_dac.set_dac_current(self.dac, 0)

```

Please read the guide about [how to create a new node](new_node_creation.md) to learn more about nodes.
This guide also contains an example for a `ScheduleNode`.

**Examples of nodes requiring an external samplespace**

- `coupler_spectroscopy` sweeps the `dc_current` which is set by the SPI rack not the cluster
- `T1` sweeps a repetition index to repeat the measurement many times
- `randomized_benchmarking` sweeps different seeds. Although the seed is a schedule parameter, sweeping outside the
  schedule improves memory utilization.
