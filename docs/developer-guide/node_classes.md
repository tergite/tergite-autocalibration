# Node classes


## The Node interface

``` mermaid
---
config:
  look: handDrawn
  theme: neutral
---
flowchart TD
  A["baseNode.calibration()"] --> B["baseNode.measure()"]
  B --> C["baseNode.post_process()"]
```

The basic Node structure consists of a `calibration()` method, a `measure()` method and a `post_process()` method.
- the  `calibration()` method is implemented at the baseNode and returns a `calibrationStatus`
- the  `measure()` method is NOT implemented at the baseNode. To allow more flexibility in how measurements are performed, the measurement type is injected for each particular node. The following section presents the details.
- the `post_process()` method is implemented at the baseNode.


## Node Categories
Each node can act either on Qubits or Couplers. In each case node attributes and methods may have different requirements so
each node implementation has to inherint either from the
`QubitNode` or the `CouplerNode` defining class.

The execution of many nodes consists of a single schedule compilation, a single measurement and a single
post-processing.
However, for more adavanced nodes where more complex measurements are needed, this workflow can become limiting.
To allow greater flexibility a class attribute in the node implementation defines the measurement type as
`ScheduleNode`, `OuterScheduleNode`, `ExternalParameterNode`. Even more measurement classes can be introduced. The only requirement is that in measurement type class must implement a `measure()` method that returns an `xarray.Dataset`


- `ScheduleNode`: The simple way of doing the measurement and having an analysis afterward. This node compiles one time
    - The quantities in the `node.schedule_samplespace` are swept in the schedule. They uploaded to the cluster all at once.
- `ExternalParameterNode`: A looping over a parameter that is external to the schedule. The measurement will be split in multiple
batches, equal to the number of the samples in the `node.external_samplespace`.
    - Both `node.schedule_samplespace`  and `node.external_samplespace` should be provided.
      As an example, the `coupler_spectroscopy` node sweeps the `dc_current` outside of the schedule:
- `OuterScheduleNode`: A looping over a parameter that although is part of the schedule, is loop outside of it. The measurement will be split again in multiple runs, equal to the number of the samples in the `node.outer_schedule_samplespace`. This type of measurement existsts only to overcome limitations in the intstructions and acquisitions memory of the Qblox Cluster.

Below, there is an example for an `ExternalParameterNode` implementation.

```python
class QubitSpectroscopyVsCurrentNode(CouplerNode):
    """
    This node performs a qubit spectroscopy measurement while varying the
    current through the coupler to measure the crossing point of the coupler with the qubit.
    """

    measurement_obj = TwoTonesMultidimMeasurement
    analysis_obj = QubitSpectroscopyVsCurrentNodeAnalysis
    measurement_type = ExternalParameterNode
    coupler_qois = ["qubit_crossing_points"]

    def __init__(self, name: str, couplers: list[str], **schedule_keywords):
        super().__init__(name, couplers, **schedule_keywords)
        self.qubit_state = 0
        self.dacs = []
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "spec_frequencies": {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            }
        }

        self.external_samplespace = {
            "dc_currents": {
                coupler: np.arange(-2.5e-3, 2.5e-3, 100e-6) for coupler in self.couplers
            },
        }
        self.validate()

    def initial_operation(self):
        pass

    def pre_measurement_operation(self, reduced_ext_space):
        first_coupler = self.couplers[0]
        self.this_current = reduced_ext_space["dc_currents"][first_coupler]
        self.spi_manager.set_dac_current(reduced_ext_space["dc_currents"])

    def final_operation(self):
        logger.info("Final Operation")
        currents = {}
        for coupler in self.couplers:
            currents[coupler] = 0

        self.spi_manager.set_dac_current(currents)
```

Please read the guide about [how to create a new node](new_node_creation.md) to learn more about nodes.
This guide also contains an example for a `ScheduleNode`.

**Examples of nodes requiring an external samplespace**

- `coupler_spectroscopy` sweeps the `dc_current` which is set by the SPI rack not the cluster
- `T1` sweeps a repetition index to repeat the measurement many times

**Examples of nodes requiring an outer schedule samplespace**
- `randomized_benchmarking` sweeps different seeds. Although the seed is a schedule parameter, sweeping outside the
  schedule improves memory utilization.
