# Tergite Automatic Calibration

![CI](https://github.com/tergite/tergite-autocalibration/actions/workflows/ci.yml/badge.svg)

A commandline application to calibrate the WACQT quantum computers automatically.  

This project contains a calibration supervisor, a collection of calibration schedules and a collection of
post-processing and analysis routines.
It is developed and tested on WACQT Quantum Computer at Chalmers University of Technology.

**This project is developed by a core group of collaborators.**    
**Chalmers Next Labs AB (CNL) takes on the role of managing and maintaining this project.**

Note: The Tergite stack is developed on a separate version control system and mirrored on GitHub.
If you are reading this on GitHub, then you are looking at a mirror. 



## Quick Start

### Dependencies

- Ensure you have [conda](https://docs.anaconda.com/free/miniconda/index.html) installed.
  (_You could simply have python +3.12 installed instead._)
- Ensure you have [redis server](https://redis.io/) running
- The standard port for a redis server is `6379`, so, this is going to be filled in the `.env` configuration later.

```shell
redis-server
```

### Installation

- Clone the repo
- If you are developing on another server e.g. the development server, please replace the url to clone

```shell
git clone git@github.com:tergite/tergite-autocalibration.git
```

- Create conda environment

```shell
conda create -n tac -y python=3.12 -y
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
acli start
```

- For more help on other commands, type:

```shell
acli --help
```

### Documentation

The documentation is maintained using [MkDocs Material](https://squidfunk.github.io/mkdocs-material/). Everytime there is a release, you can find the
documentation from the release
on [https://tergite.github.io/tergite-autocalibration](https://tergite.github.io/tergite-autocalibration).

To preview the documentation for the branch you're currently working on you first need to install the project with documentation dependencies (only needed once):

```bash
pip install -e '.[docs]'
```
Then start the live preview server of the documentation from the root of the repository:

```bash
mkdocs serve
```

and open the URL shown in the terminal (typically [http://localhost:8000/](http://localhost:8000/)) in your browser.

If you are interested to edit the documentation, please check out the documentation section in
the [contribution guidelines](CONTRIBUTING.md#documentation). There is also a page in the documentation to help you
with [writing better documentation](./docs/developer-guide/writing_documentation.html).

## Contributing to the project

If you would like to contribute to tergite-autocalibration, please have a look at our
[contribution guidelines](./CONTRIBUTING.md).

### Authors

This project is a work of
[many contributors](https://github.com/tergite/tergite-autocalibration/graphs/contributors).

Special credit goes to the authors of this project as seen in the [CREDITS](./CREDITS.md) file.

### Change log

To view the changelog for each version, have a look at
the [CHANGELOG.md](./CHANGELOG.md) file.

### License

When you submit code changes, your submissions are understood to be under the
same [Apache 2.0 License](./LICENSE.txt) that covers the project.

## Acknowledgements

This project was sponsored by:

- [Knut and Alice Wallenberg Foundation](https://kaw.wallenberg.org/en) under
  the [Wallenberg Center for Quantum Technology (WACQT)](https://www.chalmers.se/en/centres/wacqt/) project
  at [Chalmers University of Technology](https://www.chalmers.se)
-   [Nordic e-Infrastructure Collaboration (NeIC)](https://neic.no) and [NordForsk](https://www.nordforsk.org/sv) under the [NordIQuEst](https://neic.no/nordiquest/) project
-   [European Union's Horizon Europe](https://research-and-innovation.ec.europa.eu/funding/funding-opportunities/funding-programmes-and-open-calls/horizon-europe_en) under the [OpenSuperQ](https://cordis.europa.eu/project/id/820363) project
-   [European Union's Horizon Europe](https://research-and-innovation.ec.europa.eu/funding/funding-opportunities/funding-programmes-and-open-calls/horizon-europe_en) under the [OpenSuperQPlus](https://opensuperqplus.eu/) project
 