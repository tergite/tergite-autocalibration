# Operation

The package ships with a CLI called `acli` (autocalibration command line interface) to solve some common tasks that
appear quite often.
In the following there are a number of useful commands, but if you want to find out information about commands in your
shell use `acli --help`.

Since some of the commands below are using autocompleting in most cases you would have to enable that feature in your
shell by running:

```bash
acli --install-completion
```

Usually the shell would just suggest you file paths when pressing the tabulator, but with autocompletion enabled, you
would be even get suggestions for node names or other inputs depending on your configuration.

## CLI ##

This section provides an overview of the Command Line Interface (CLI) options and their functionalities.

### Main Commands ###

The autocalibration CLI is organized into several main command groups:

- `start`: Run the automatic calibration according to the provided config files
- `cluster`: Handle operations related to the cluster
- `spi`: Handle operations related to the spi rack
- `node`: Handle operations related to the node
- `graph`: Handle operations related to the calibration graph
- `config`: Load and save the configuration files
- `browser`: Will open the dataset browser, which makes you view the datasets from measurements
- `redis`: Operations to handle redis values
- `joke`: Handle operations related to the well-being of the user

### Calibration Commands

#### `start`

Starts the calibration supervisor.

**Usage:**

```bash
acli start [OPTIONS]
```

**Options:**

- `-d TEXT`: Dummy mode. The calibration chain runs as normal but the returned datasets are dummy.
  The generation of each dummy dataset takes into account the existing redis config and the provided samplespaces.
- `-c TEXT`: Cluster IP address (if not set, it will use CLUSTER_IP from the .env file)
- `-r TEXT`: Rerun an analysis (specify the path to the dataset folder)
- `-n, --name TEXT`: Specify the node type to rerun (works only with -r option)
- `--browser`: Will open the dataset browser in the background and plot the measurement results live

### Cluster Commands ###

#### `cluster reboot` ####

Reboots the cluster.

**Usage:**

```
acli cluster reboot
```

This command will prompt for confirmation before rebooting the cluster, as it can interrupt ongoing measurements.

### SPI Rack Commands ###

#### `spi status` ####

Prints information about the current currents on the spi rack.
Only couplers that are having a DAC in the SPI configuration are considered.
Please check the [documentation about configuration](./configuration_files.md) about how to change the SPI DACs.

**Usage:**

```
acli spi status
```

#### `spi status` ####

Resets all currents on the SPI rack to 0.
Only couplers that are having a DAC in the SPI configuration are considered.
Please check the [documentation about configuration](./configuration_files.md) about how to change the SPI DACs.

**Usage:**

```
acli spi reset
```

### Node Commands ###

#### `node reset` ####

Resets all parameters in Redis for the specified node(s).

**Usage:**

```
acli node reset [OPTIONS]
```

**Options:**

- `-n, --name TEXT`: Name of the node to be reset in Redis (e.g., resonator_spectroscopy)
- `-a, --all`: Reset all nodes
- `-f, --from_node TEXT`: Reset all nodes from the specified node in the chain

### Graph Commands ###

#### `graph plot` ####

Plots the calibration graph to the user-specified target node in topological order.

**Usage:**

```
acli graph plot
```

This command visualizes the calibration graph using an arrow chart.

### Configuration Commands

#### `config load`

Load the configuration.

**Usage:**

```bash
acli config load [OPTIONS]
```

**Options:**

- `-f/--filepath`: Path to the configuration package to load. It can be either to the `configuration.meta.toml`
  file or to a zip file containing the whole configuration.
- `-t/--template`: Path to the template package to load. The templates are located in
  `tergite_autocalibration.config.templates`. If the autocompletion is installed for `acli`, then the templates should
  be shown as suggestions automatically.

**Notes:**

To run this command, please navigate to the root directory of the repository.
The configuration package will be placed into the root directory, which is the default location for the application to
detect the configuration package.

#### `config save`

**Usage:**

```bash
acli config save [OPTIONS]
```

Save the configuration.

**Options:**

- `-f/--filepath`: Path to the configuration package to save. If the path name is ending with `.zip`, it will
  automatically create a zip file and treat it as if you are running with `-z`.
- `-z/--as-zip`: Will make the configuration file be a zip archive.

#### `bcc-export`

**Usage:**

```bash
acli bcc-export [OPTIONS]
```

Create a `calibration_seed.toml` file that can be used from the backend to push calibration values to the database.

**Options:**

- `-q/--qubits`: Qubit input e.g. `"q00,q01,q02,q03,q04"` or `"q01-q05"` or `"q01-q06, q08"`.
  If the input is an integer e.g. 3, it will generate `"q01,q02,q03"`.
- `-c/--couplers`: Couplers to export e.g. `"q00_q01"` as comma-separated list
- `-o/--output-file`: calibration_seed.toml to write.

#### `config generate`

**Usage:**

```bash
acli config generate [OPTIONS]
```

Save the configuration.

**Options:**

- `-h/--host`: Host address where to run the interface of the generator. Default: 127.0.0.1
- `-p/--port`: Port on which the application will serve the generator. Default: 8079

### Dataset browser ###

#### `browser` ####

Starts the dataset browser.

**Usage:**

```
acli browser --datadir [OPTIONS]
```

**Options:**

- `--datadir PATH`: Folder to take the plot data from
- `--liveplotting`: Whether plots should be updated in real time (default: False)
- `--log-level INT`: Log-level as in the Python `logging` package to be used in the logs (default: 30)

### Redis handling ###

#### `redis` ####

Tools to work with the redis backend.

**Usage:**

```
acli redis save-file [FILENAME]
```

Store a backup of redis in .json format.

**Usage:**

```
acli redis load-file [FILENAME]
```

Load a backup of redis from a .json format.
The file must follow the standard from the `acli redis save-file` function.

### Joke Command ###

#### `joke` ####

Prints a random joke to lighten the mood.

**Usage:**

```
acli joke
```

This command fetches and displays a random joke, excluding potentially offensive content.

### Notes ###

- The CLI uses the Python library `typer` for command-line interface creation.
- Some commands may require additional configuration or environment variables to be set.
- When using the `-r` option for rerunning analysis, make sure to also specify the node name using `-n`.

For more detailed information about each command, use the `--help` option with any command or subcommand.
