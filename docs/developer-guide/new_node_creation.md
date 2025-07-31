# Creating a new node

This tutorial is about how to create a new node class.
The word node is an overloaded term, used in many contexts, so, what does a node mean here?
If you put all steps to characterize a qubit in a chain, then it could be seen as a directed graph with the calibration
steps as nodes.
Take a look at the [node overview](../node-library/available_nodes.md) to get an impression on how it looks like.
In this guide, we will cover the topics:

1. File locations for nodes within the framework
2. How to implement a node
3. Register the node in the framework

Following these steps, you can easily contribute to the automatic calibration with your own nodes in a couple of hours.

## Base classes
The base classes on which all nodes are built can be found in `tergite_autocalibration/lib/base`.
There are base classes for all three components of a node, the node itself, the measurement and the analysis.

Nodes can be either `QubitNode` or `CouplerNode`, both inherit from a `BaseNode` class providing common interfaces and functionalities. They will have different quantities of interest depending on the type (qubit_qoi for QubitNode)
A Node also need to implement a Schedule; there are two files in `tergite_autocalibration/lib/nodes`
- `ScheduleNode`: A node with a simple sweep over the samplespace. The quantify schedule is only compiled once and the
  parameter values from the samplespace are the input for the schedule function of the measurement.
- `ExternalParameterNode`: A node with a more complex measurement procedure. It allows to run multiple steps sequentially, where each step might require recompilation of the schedule. There is an external parameter involved (the current applied to the coupler using the SPIRack), which is the part of the generating function within the schedule. There can be a fixed schedule or a schedule varying at each iteration (for example when changing value in the schedule when changing current). The latter can also handle elements (couplers or qubits) having different number of iterations.

Both files provide classes with multiple inheritance that combine type and schedule, i.e. `ScheduleQubitNode` or `ExternalParameterFixedScheduleCouplerNode`, 
that can be used in nodes to simplify implementation of new nodes for developers.

Measurements only have a base class providing a common interface.

Analysis classes have a more complex composition and inheritance structure. The entry point is always a `BaseNodeAnalysis` class, implemented in the `BaseAllCouplersAnalysis` or `BaseAllQubitsAnalysis` classes. Each node analysis will loop over all elements (qubits or couplers) defining a relevant analysis class, either QubitAnalysis or CouplerAnalysis. These analyses will have a common structure with a setup phase (where all dataset information is read and processed), a property that returns a quantity of interest (QOI) object, and then a call to a function updating the REDIS database.
The analysis will be very node specific. CouplerAnalysis classes combine information from two QubitAnalyses; information can be stored both at the coupler level, for example all CZ gate information, or at the qubit level within the coupler (in REDIS couplers:coupler_name:qubit_name:qubit_information). This allows to handle information for the same qubit when used in different couplers. Plots are also handled in the analysis class, with the Qubit/Coupler analyses handling plotting according to the information required (i.e. plotting all qubits in a resonator_spectropy, both qubits in all couplers in a coupler_spectroscopy, or a single plot per coupler for two qubit gate randomized benchmarking).

## Where are the nodes located?

The nodes are located in `tergite_autocalibration/lib/nodes`.
If you open that module, you will find that there are four submodules for different kind of nodes:

- `characterization`: For nodes such as the T1, T2 or the randomized benchmarking.
- `coupler`: For all nodes that are related to a two-qubit setup with a coupler.
- `qubit_control`: All nodes that calibrate a quantity of interest for the qubit.
- `readout`: All nodes that calibrate a quantity of interest for the resonator.

Please create a new submodule for your node in one of the four submodules listed above.
Essentially, a proper package in the end should contain:

- `__init__.py`: This is an empty file to mark that the folder is a package. Please add this file, because otherwise
  your classes cannot be found.
- `node.py`: A file where the definition of the node class goes.
- `analysis.py`: A file where the analysis object is defined.
- `measurement.py`: Contains the measurement object with the schedule.
- `tests`: A folder with all test function and test data. Read more about [unit tests](unit_tests.md) to find out on
  how to structure them.
- `utils`: A folder in case you have defined very specific helper classes.

Before we are going to a look on how this would be implemented in detail, a quick note on naming conventions.

### Naming conventions

Since we are creating a lot of node, measurement and analysis objects, there are some naming conventions to make it more
standardized and understandable to learn the framework.
Taking the rabi oscillations as an example, we have:

- `rabi_oscillations`: This is the **node name**, which is used in the commandline interface or for other purposes to
  pass the node name as a string.
- `RabiOscillations`: This is the name of the **node class**.
- `RabiOscillationsNodeAnalysis`: The name of the respective **analysis class for that node**.
- `RabiOscillationsMeasurement`: And the name of the respective **measurement class**.

When there are some more complicated nodes for which you do not know how to name it, please just take a look at the
already existing nodes and make a guess how it feels to name it correctly.
Also, when there is a node that starts with an abbreviation, please have all letter for the abbreviation capitalized
e.g.:
`cz_calibration` would be the node name for the `CZCalibration` node class.

## Node implementation details

All node classes are supposed follow the same interface as described in the `BaseNode`class.
Below, for example, you have the rabi oscillations node:

```python
import numpy as np

from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.lib.nodes.qubit_control.rabi_oscillations.measurement import RabiOscillationsMeasurement
from tergite_autocalibration.lib.nodes.qubit_control.rabi_oscillations.analysis import RabiQubitAnalysis

class RabiOscillationsNode(ScheduleQubitNode):
  measurement_obj = RabiOscillationsMeasurement
  analysis_obj = RabiQubitAnalysis
  qubit_qois = ["rxy:amp180"]

  def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
    super().__init__(name, all_qubits, **schedule_keywords)
    self.schedule_samplespace = {
      "mw_amplitudes": {
        qubit: np.linspace(0.002, 0.90, 61) for qubit in self.all_qubits
      }
    }
```

As you can see, it inherits from the `ScheduleQubitNode` class, which contains a very simple definition of a node that runs a
simple sweep over a single quantity for all qubits defined in the run_config.
More information about other node classes can be found in the description of the base classes above.
Furthermore, you can see that the node has three class attributes:

- `measurement_obj`: Contains the class of the measurement, that defines the pulse schedule for the instruments
- `analysis_obj`: Contains the class for the analysis to post-process the measurement results. For example, this could
  be a simple fitting function.

Also, you can see in the constructor, there is an attribute called `schedule_samplespace`.
Here, we define in the measurement, what quantity will be swept over.

### Creating a `measurement_obj`

The `measurement_obj` is implemented in the `measurement.py` file of your node submodule.
To initialize we require a dictionary of the extended transmons:

`transmons: dict[str, ExtendedTransmon]`

It must contain a method called `schedule_function` that expects the node's samplespace as input and returns the
complete schedule.

### Creating an `analysis_obj`

The `analysis_obj` is implemented in the `analysis.py` file from your module and contains the class that perform the
analysis. See the description in the Base classes above to understand which classes need to be implemented and which base classes to use.

Some useful information:
- Node analyses will simply loop over Qubit/Coupler analyses and will automatically deal with high level events such as plotting and saving to REDIS. Operations can be overloaded if a node has specific needs. The most common custom operation at this level is the definition of which additional plots are plotted.
- Coupler/Qubit analyses have two steps, setup (dataset handling) and analysis. 
- Analyses return an object called Quantity Of Interest (QOI) which is a dictionary with a success boolean variable and a dictionary called  analysis result that can stored any type of information. Normally the QOI have the same names of the redis fields but this is not mandatory. For example in the cz_calibration_analysis the QOIs are different from the redis_fields defined in the dynamic calibration nodes.
- In addition to the standard plots that are displayed, there is another function called `save_other_plots` that can be implemented in each analysis to plot additional figures. This can be extremely useful for debugging and for visualizing additional information, for example in coupler nodes dealing with multiple working points. 
- Information can be stored in REDIS for each qubit in a coupler. This is done using this structure in the analysis result of the QOI:
```python
        analysis_result = {
            self.name_qubit_1: (dict(zip(self.redis_fields, q1result))),
            self.name_qubit_2: (dict(zip(self.redis_fields, q2result))),
        }
```
An example can be found in the coupler spectroscopy and in the coupler resonator spectroscopy coupler analyses.

### Node types and samplespaces

In the example above, the node inherits from the class `ScheduleNode`.
This is one option for the node behaviour:

- `ScheduleNode`: A node with a simple sweep over the samplespace. The quantify schedule is only compiled once and the
  parameter values from the samplespace are the input for the schedule function of the measurement.
- `ExternalParameterNode`: A node with a more complex measurement procedure. It allows to run multiple steps
  sequentially, where each step might require recompilation of the schedule. There is an external parameter involved,
  which is the part of the generating function within the schedule.

When you are implementing a node, you can choose which of the two abstract node classes fit better with the behaviour of
your new node. Also, if you want to implement a more sophisticated measurement procedure, you can override the
procedures in the measurement function or in other places. Check out the article about [node classes](node_classes.md)
for more details.

## Register the node in the framework

To add the node to the framework, you have to register it in two places - the node factory and the calibration graph.
Also, please do not forget to write documentation for your node.

### Node factory

A factory is a programming pattern to create complex objects such as our nodes in a bit more clearly interfaced way.
The factory contains a register for all nodes, that map their name to the respective class where the node is
implemented.
When you are adding a node, please register your node name, by adding it to the
`tergite_autocalibration.lib.utils.node_factory.NodeFactory` class under the `self.node_name_mapping` attribute in the
dictionary.

### Calibration graph

In the file `tergite_autocalibration/lib/utils/graph.py` in the list `graph_dependencies` insert the edges that
describe the position of the new node in the Directed Acyclic Graph. There are two entries required (or one entry if
the new node is the last on its path):

- `('previous_node','new_node')`
- `('new_node', 'next_node')`

It is possible to have multiple dependencies, i.e. a node can be set to run only if two different nodes are run.

- `('previous_node_1','new_node')`
- `('previous_node_2','new_node')`

This will result in both `previous_node_1` and `previous_node_2` to be run before the `new_node`.

### Documentation

Please add your node to the [list of available nodes](../node-library/available_nodes.md) in this documentation.

If possible, please create a separate page explaining your node's functionality and link it there. Include relevant information about:

- How to use your node
- Required dependencies
- References to publications (if applicable)
- Any other details needed for others to use your code

### Figures

Figure are managed from the figure_util.py file in the util folder of the base node directory. 
All figure should be created by provided utility function to assure consistent formatting.
It is possible to create additional figure by implementing the "save_other_plots" function in your analysis node.
Please create the new figure using this utility function. The typical usage is to display all 1D distributions when performing a 2D scan.
An example can be found in the punchout node.

For implementation details, refer to the [Node types section](node_classes.md).