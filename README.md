# tergite-autocalibration

![CI](https://github.com/tergite/tergite-autocalibration/actions/workflows/ci.yml/badge.svg)

A commandline application to calibrate the Swedish quantum computers automatically.  

This project contains an orchestration manager, a collection of calibration schedules and a collection of post-processing & analysis routines.  
It was developed and tested on WACQT quantum computer at Chalmers university of Technology.

**This project is developed by a core group of collaborators.**    
**Chalmers Next Labs AB (CNL) takes on the role of managing and maintaining this project.**

## Version Control

The tergite stack is developed on a separate version control system and mirrored on Github.
If you are reading this on GitHub, then you are looking at a mirror. 


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
[many contributors](https://github.com/tergite/tergite-autocalibration/graphs/contributors).

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
 