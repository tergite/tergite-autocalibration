# Configuration

To run the autocalibration you will need to configure it with a couple of different configuration files.
Doing the configuration with a pre-built configuration package will take just some minutes.
On an unknown experimental device without pre-built files, it probably takes slightly longer.

After reading this guide, you will know:

- How to set basic environment variables
- What is a configuration package and how is it structured

Take a look into the operation manual to
see [how to load and save configuration packages](operation.md#configuration-commands).

## Environment variables

Computer systems generally use variables on a system level e.g. to store global variables.
These variables usually have a name with `UPPER_CASE_LETTERS`.
Also, there is a convention to store those variables in a `.env` file on the root-level of your project and load the
variables before running a program.
The template for the environmental variables of the tergite-autocalibration can be found in the `.example.env` file on
root-level of the repository.
E.g. if you have cloned the repository into `/home/user/repos/tergite-autocalibration`, then your example template
should be located there.

Copy the template and update values according to the instructions. The template file itself provides instructions on how
to update the values.

```bash
cp .example.env .env
```

Values that can be set in the environment are e.g. `PLOTTING` and this variable determines whether plots should be
shown.
Most of the values have reasonable defaults, but of course the `CLUSTER_IP` is required when you measure on a cluster
and do not want to run only on dummy data.

## Configuration packages

For all other configuration, there is a so-called configuration package.
The reason to have a configuration package is to have all configuration files in one place.

This is how an example configuration package looks like:

- `configs/`: A folder with the configuration files
  - `cluster_config.json`: The configuration for the cluster
  - `device_config.toml`: The configuration with values related to the device/chip
  - `node_config.toml`: Some device configuration that is overwritten when a certain node is executed
  - `run_config.toml`: Run-specific parameters such as the qubits and the target node to calibrate
  - `spi_config.toml`: Defines the spi and groups of couplers
  - `user_samplespace.py`: Define custom sweeps for the nodes
- `additional_files/`: A folder with other additional files
  - `mixer_calibration.csv`: E.g. the mixer calibration values
- `wiring_diagrams/`: A folder with even more additional files
  - `wiring_diagram.png`: E.g. a wiring diagram
- `configuration.meta.toml`: The configuration file that describes the structure of the configuration package

The templates for a full configuration package can be found in `tergite_autocalibration/config/templates`.
There is a `.default` template to illustrate the general structure of a configuration package.
Furthermore, there are some pre-build configuration packages for different kind of setups.

For a configuration to be detected by the application, the `configuration.meta.toml` file should be placed in the root
folder of the tergite-autocalibration repository.
All filepaths relative to the configuration files have to be able to be resolved.
Now, we will go through all the details of these configuration files.

### The configuration.meta.toml file

This is the file that always has to be part of the configuration package.
It tells the machine where all other configuration files are located, which is crucial to make the automatic loading and
saving work.
A very simple version of the `configuration.meta.toml` belonging to the screenshot above would look like this:

```toml
path_prefix = 'configs'

[files]
cluster_config = 'cluster_config.json'
device_config = 'device_config.toml'
node_config = 'node_config.toml'
run_config = 'run_config.toml'
spi_config = 'spi_config.toml'
user_samplespace = 'user_samplespace.py'

[misc]
mixer_calibrations = "additional_files"
wiring_diagrams = "wiring_diagrams"
```

The main sections in that `.toml` file are:

- `path_prefix`: This refers to the folder name into which you would put the other configuration files.
  If you leaved it empty, this would mean that all configuration files would be inside the same folder with
  the `configuration.meta.toml` file.
- The `files` section: Here, you put the paths to the configuration files.
  It can be one or more of the six above.
  For example, you could also just define `cluster_config` and `device_config` and it would be still a valid
  configuration package.
  However, maybe during runtime, it would break the code.
  E.g. if you run without a cluster configuration, it could work fine if you are running a dummy measurement without
  real hardware, but if you want to measure on real hardware, you would need the cluster configuration.
  More about the configuration files is described in the sections below for each of the files individually.
- The `misc` section: You can add as many folder as you want to that section.
  Here, we are adding one more folder to the configuration package with additional files.
  This section is meant to add files like mixer corrections or a wiring diagram, which do not follow a well-defined
  standard, but might be useful information to be transferred with the configuration package.

Since the `configuration.meta.toml` file always should reflect how the configuration package looks like, please update
it as soon as you add or delete any configuration files from your package.

Now, in the folder, there are these six configuration files:

- Cluster configuration
- Device configuration
- Node configuration
- Run configuration
- SPI configuration (optional, only required for two-qubit calibration)
- Custom user samplespace configuration (optional, only required if you are sweeping on a very specific range of
  parameters)

In the following, there are some more detailed descriptions of what these files mean and contain.
More information can also be found in the templates and example configuration files.

### Cluster configuration (.json):

A QBLOX cluster consists of a couple of modules of which each can have multiple input/output options for SMI cables.
In the cluster configuration the connection is made between these QBLOX cluster physical ports and clocks to the qubits
and couplers of the QPU.

Example: Part of a cluster definition

```json
{
  "config_type": "quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig",
  "hardware_description": {
    "clusterA": {
      "instrument_type": "Cluster",
      "ref": "internal",
      "modules": {
        "2": {
          "instrument_type": "QCM_RF"
        },
        "10": {
          "instrument_type": "QRM_RF"
        }
      }
    }
  },
  "hardware_options": {
    "modulation_frequencies": {
      "q00:mw-q00.01": {
        "lo_freq": 3946000000.0
      },
      ...
    },
    "mixer_corrections": {
      "q00:mw-q00.01": {
        "dc_offset_i": 0.0,
        "dc_offset_q": 0.0,
        "amp_ratio": 1.0,
        "phase_error": 0.0
      },
      ...
    }
    },
  "connectivity": {
    "graph": {
      "directed": false,
      "multigraph": false,
      "graph": {},
      "nodes": [
        {
          "instrument_name": "clusterA",
          "id": "clusterA.module2.complex_output_0"
        },
        ...
      ],
      "links": [
        {
          "source": "clusterA.module2.complex_output_0",
          "target": "q00:mw"
        },
        ...
      ]
    }
    }
}
```

The file in the template package is `cluster_configuration.json`.

You can find more information about the hardware configuration in
the [documentation of quantify-scheduler](https://quantify-os.org/docs/quantify-scheduler/tutorials/Compiling%20to%20Hardware.html)

**Migrating old hardware configurations to match quantify-scheduler>=0.18.0**

With quantify-scheduler 0.18.0 there has been introduced a new way on how to structure the hardware configuration file.
If you are having a hardware configuration file, that is structured using the old way, you can use the following script
to migrate it to the new structure.

```bash
python tergite_autocalibration/scripts/migrate_blox_hardware_configuration.py <PATH_TO_HW_CONFIG>
```


### Device Configuration file (.toml):

While the previous two configuration files have been used to configure the room temperature instruments, the device
configuration defines the initial parameters and characteristics of chip itself.
The device configuration is having two main sections -- the `[device]` and the `[layout]` section.
In the `[device]` section prior knowledge about the device from the VNA are set for the resonator, qubit (drive) and the
coupler.

It is possible to either address a qubit individually, e.g. the following would set the VNA frequency for qubit `q06`:

```toml
[device.resonator.q06]
VNA_frequency = 6832973301.189378
```

or for all qubits:

```toml
[device.resonator.all]
attenuation = 12

[device.qubit.all]
measure.integration_time = 2.5e-6
measure_1.integration_time = 2.5e-6
measure_2.integration_time = 2.5e-6
rxy.duration = 28e-9
```

In the `[layout]` section the positions of the qubits can be set.
This is useful if one would like to e.g. plot the device.
Qubits have an x (column) and a y (row) position:

```toml
[layout.resonator.q06]
position = { column = 0, row = 0 }
```

### Run configuration (.toml):

In this file there are some settings such as the target node, the qubits and the couplers to calibrate.

Example: Calibrate qubits `q01` and `q02` with coupler `q01_q02` up until the node `cz_calibration`.

```toml
target_node = "cz_calibration"
qubits = ["q01", "q02"]
couplers = ["q01_q02"]
```

### Node configuration (.toml):

Below, you can define node-specific parameters setting `[node_name.scope.property]` where scope are the qubits/couplers
and the property is a property known to the node.
This would load and overwrite the configurations made in the device configuration.

Example: Setting the reset duration for the resonator spectroscopy node.

```toml
[resonator_spectroscopy.all]
reset.duration =  60e-6
```

The file in the template package is `node_config.toml`.

### SPI configuration (.toml):

When working with two-qubit gates, there has to be a current source for the coupler and in the QBLOX stack this is
coming from the so called SPI rack.
The SPI configuration is mapping the qubits to their respective modules in the SPI rack and can be further used to
assign the couplers to groups.

Example: Definition of a coupler

```toml
[couplers.q11_q12]
spi_module_no = 1
dac_name = "dac0"
edge_group = 1
```

The file in the template package is `spi_config.toml`.

### Custom user samplespace configuration (.py):

If you want to generate samplespaces with your own custom Python scripts, you can add a custom user samplespace
configuration.
The file must contain the definition of your samplespace according to the following schema:

```python
user_samplespace = {
    node1_name : {
            "settable_of_node1_1": { 'q01': np.ndarray, 'q02': np.ndarray },
            "settable_of_node1_2": { 'q01': np.ndarray, 'q02': np.ndarray },
            ...
        },
    node2_name : {
            "settable_of_node2_1": { 'q01': np.ndarray, 'q02': np.ndarray },
            "settable_of_node2_2": { 'q01': np.ndarray, 'q02': np.ndarray },
            ...
        }
}
```

Please note: Do not rename the variable `user_samplespace`, because it cannot be imported otherwise.

The file in the template package is `user_samplespace.py`.

## Next steps

Read about the commandline interface, which contains a chapter
about [how to load and save configuration packages](operation.md#configuration-commands).