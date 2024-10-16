# tergite-autocalibration

![CI](https://github.com/tergite/tergite-autocalibration/actions/workflows/ci.yml/badge.svg)

A commandline application to calibrate the WACQT quantum computers automatically.  

This project contains a calibration supervisor, a collection of calibration schedules and a collection of post-processing & analysis routines.  
It was developed and tested on WACQT Quantum Computer at Chalmers University of Technology.

**This project is developed by a core group of collaborators.**    
**Chalmers Next Labs AB (CNL) takes on the role of managing and maintaining this project.**

## Version Control

The Tergite stack is developed on a separate version control system and mirrored on GitHub.
If you are reading this on GitHub, then you are looking at a mirror. 


## Dependencies

- [Python 3.9+](https://www.python.org/)
- [Redis](https://redis.io/)

## Quick Start

- Ensure you have [conda](https://docs.anaconda.com/free/miniconda/index.html) installed. 
 _(You could simply have python +3.9 installed instead.)_
- Ensure you have a [redis server](https://redis.io/) instance running
- The standard port for a redis server is `6379`, so, this is going to be filled in the `.env` configuration later.

```shell
redis-server
```

- Clone the repo

```shell
git clone git@github.com:tergite/tergite-autocalibration.git
```

- Create conda environment

```shell
conda create -n tac -y python=3.9
conda activate tac
```

- Install the application

```shell
cd tergite-autocalibration
pip install -e .
```

- Copy the `.example.env` file to `.env` and 
  update the environment variables there appropriately.
- Check out the section about configuration about which other configuration files have to be edited.

```shell
cp .example.env .env
```

- Start the automatic calibration

```shell
acli calibration start
```

- For more help on other commands, type:

```shell
acli --help
```

## Configuration
To run the calibration, make sure to have the following configuration files in place:

- [`.example.env`](.example.env) Global parameters for the calibration e.g. the IP address of the cluster and paths to other configuration files.

- [`device_config.toml`] Initial configuration like VNA values for the device.

- [`cluster_config.toml`] The hardware configuration for the QBlox cluster.

- [`spi_config.toml`] The configuration for the SPI rack (only necessary if you are running two qubit calibrations).

- [`calibration_config.toml`] Define which qubits/couplers are calibrated and what are the calibration parameters for a specific node.


Configuration packages for specific devices can be found in `data/devices`.


## Official documentation

The documentation is maintained in using [Quarto](https://quarto.org/). The documentation for the public version of the code is available [here](https://tergite.github.io/tergite-autocalibration/getting_started.html). 
To visualise the latest version of the documentation, install Quarto locally and build the website to browse the documentation. Make sure to have quarto in your PATH before you crate the conda environment to simplify its use in VSCode. You can install the Quarto extension 


## Contribution Guidelines

If you would like to contribute to tergite-autocalibration, please have a look at our
[contribution guidelines](./CONTRIBUTING.md)

## Authors

This project is a work of
[many contributors](https://github.com/tergite/tergite-autocalibration/graphs/contributors).

Special credit goes to the authors of this project as seen in the [CREDITS](./CREDITS.md) file.

## Changelog

To view the changelog for each version, have a look at
the [CHANGELOG.md](./CHANGELOG.md) file.

## License

[Apache 2.0 License](./LICENSE.txt)

## Acknowledgements

This project was sponsored by:

-   [Knut and Alice Wallenberg Foundation](https://kaw.wallenberg.org/en) under the [Wallenberg Center for Quantum Technology (WACQT)](https://www.chalmers.se/en/centres/wacqt/) project at [Chalmers University of Technology](https://www.chalmers.se)
-   [Nordic e-Infrastructure Collaboration (NeIC)](https://neic.no) and [NordForsk](https://www.nordforsk.org/sv) under the [NordIQuEst](https://neic.no/nordiquest/) project
-   [European Union's Horizon Europe](https://research-and-innovation.ec.europa.eu/funding/funding-opportunities/funding-programmes-and-open-calls/horizon-europe_en) under the [OpenSuperQ](https://cordis.europa.eu/project/id/820363) project
-   [European Union's Horizon Europe](https://research-and-innovation.ec.europa.eu/funding/funding-opportunities/funding-programmes-and-open-calls/horizon-europe_en) under the [OpenSuperQPlus](https://opensuperqplus.eu/) project
 