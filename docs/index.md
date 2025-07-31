# Documentation of the Tergite Automatic Calibration

The tergite-autocalibration is a toolkit to ease calibrating quantum devices for superconducting platforms.
The project contains an orchestration manager, a collection of calibration schedules and a collection of post-processing
and analysis routines.
It is tailored to tune-up the 25 qubits QPU at Chalmers, which is receiving generous funding by the Wallenberg
Centre for Quantum Technology ([WACQT](https://wacqt.se)) for research, development and operation.

### [User Guide](user-guide/getting_started.md)

A tutorial on how to get started with the automatic calibration.
This tutorial contains a guide on how to use the commandline interface with quick commands.
Further, there is an introduction into configuration files.

- [Getting started](user-guide/getting_started.md)
- [Operation](user-guide/operation.md)
- [Configuration Files](user-guide/configuration_files.md)

### [Node Library](node-library/available_nodes.md)

The main principle behind the automatic calibration is based on calibrating nodes in a graph structure.
A node contains all the measurement and analysis classes to find the quantity of interest - for qubits and couplers.
If you are interested in implementing a new node, it might be worth it to check whether there are existing nodes that
you can use to find the qubit properties you are looking to calibrate.

### [Developer Guide](developer-guide/developer_guide.md)

This repository is an actively developed open-source project and also part of the [Tergite](https://tergite.github.io)
full-stack software ecosystem to operate a quantum
computer.
Hence, you are more than welcome to contribute to the project with your own ideas that fit into the framework.
To familiarize yourself with the existing classes and the architecture of the automatic calibration, please take a look
into the development guide.
Here, you can also find best practices and information about our design philosophy.

- [Create node classes](developer-guide/new_node_creation.md)
- [Write unit tests](developer-guide/unit_tests.md)
- [Documentation guidelines](developer-guide/writing_documentation.md)