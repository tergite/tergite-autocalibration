# tergite-calibration

![CI](https://github.com/tergite/tergite-calibration/actions/workflows/ci.yml/badge.svg)

A commandline application to calibrate QAL 9000-Like quantum computers automatically

**THIS CODE IS OPEN SOURCE AND PUBLIC. BY CONTRIBUTING TO IT, YOU ACCEPT THAT YOUR CONTRIBUTIONS WILL BE LICENSED 
VIA THE [APACHE 2.0 LICENSE](./LICENSE.txt)**

This project contains an orchistration manager, a collection of callibration schedules and a collection of post-processing & analysis routines.  
It is tailored for the tune-up of the 25 qubits QPU at Chalmers, QTL.  

## Dependencies

- [Python 3.9+](https://www.python.org/)
- [Redis](https://redis.io/)

## Quick Start

- Ensure you have [conda](https://docs.anaconda.com/free/miniconda/index.html) installed. 
 (_You could simply have python +3.8 installed instead._)
- Ensure you have [redis server](https://redis.io/) running

```shell
redis-server
```

- Clone the repo

```shell
git clone git@github.com:tergite/tergite-calibration.git
```

- Create conda environment

```shell
conda create -n tac -y python=3.9
conda activate tac
```

- Install the application

```shell
cd tergite-calibration
pip install -e .
```

- Copy the `dot-env-template.txt` file to `.env` and 
  update the environment variables there appropriately.

```shell
cp dot-env-template.txt .env
```

- Start the automatic calibration

```shell
acli calibration start
```

- For more help on other commands, type:

```shell
acli --help
```

## Contribution Guidelines

If you would like to contribute to tergite-webgui, please have a look at our
[contribution guidelines](./CONTRIBUTING.md)

## Authors

This project is a work of
[many contributors](https://github.com/tergite/tergite-calibration/graphs/contributors).

Special credit goes to the authors of this project as seen in the [CREDITS](./CREDITS.md) file.

## ChangeLog

To view the changelog for each version, have a look at
the [CHANGELOG.md](./CHANGELOG.md) file.

## License

[Apache 2.0 License](./LICENSE.txt)

## Acknowledgements

This project was sponsored by:

-   [Knut and Alice Wallenburg Foundation](https://kaw.wallenberg.org/en) under the [Wallenberg Center for Quantum Technology (WAQCT)](https://www.chalmers.se/en/centres/wacqt/) project at [Chalmers University of Technology](https://www.chalmers.se)
-   [Nordic e-Infrastructure Collaboration (NeIC)](https://neic.no) and [NordForsk](https://www.nordforsk.org/sv) under the [NordIQuEst](https://neic.no/nordiquest/) project
-   [European Union's Horizon Europe](https://research-and-innovation.ec.europa.eu/funding/funding-opportunities/funding-programmes-and-open-calls/horizon-europe_en) under the [OpenSuperQ](https://cordis.europa.eu/project/id/820363) project
-   [European Union's Horizon Europe](https://research-and-innovation.ec.europa.eu/funding/funding-opportunities/funding-programmes-and-open-calls/horizon-europe_en) under the [OpenSuperQPlus](https://opensuperqplus.eu/) project
 