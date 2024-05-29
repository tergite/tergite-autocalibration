# Contributing to tergite-calibration

**This project is currently not accepting pull requests from the general public yet.**

**It is currently being developed by the core developers only.**

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

-   Reporting a bug
-   Discussing the current state of the code
-   Submitting a fix
-   Proposing new features
-   Becoming a maintainer

## Versioning

When versioning we follow the format `{year}.{month}.{patch_number}` e.g. `2023.12.0`.

## We Develop with Github

We use Github to host code, to track issues and feature requests, as well as accept pull requests.

But We Use [Github Flow](https://docs.github.com/en/get-started/quickstart/github-flow),
So All Code Changes Happen Through Pull Requests

Pull requests are the best way to propose changes to the codebase (we
use [Github Flow](https://docs.github.com/en/get-started/quickstart/github-flow)). We actively welcome your pull
requests:

1. Clone the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Any contributions you make will be under the Apache 2.0 Software Licenses

In short, when you submit code changes, your submissions are understood to be under the
same [Apache 2.0 License](./LICENSE.txt) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](https://github.com/tergite/tergite-calibration/issues)

We use Github issues to track bugs. Report a bug
by [opening a new issue](https://github.com/tergite/tergite-calibration/issues); it's that easy!

## Write bug reports with detail, background, and sample code

[This is an example](http://stackoverflow.com/q/12488905/180626).
Here's [another example from Craig Hockenberry](http://www.openradar.me/11905408).

**Great Bug Reports** tend to have:

-   A quick summary and/or background
-   Steps to reproduce
    -   Be specific!
    -   Give sample code if you can.
-   What you expected would happen
-   What actually happens
-   Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People _love_ thorough bug reports. I'm not even kidding.

## License

By contributing, you agree that your contributions will be licensed under its Apache 2.0 License.

## How to Use

-   Make sure you have [conda](https://docs.anaconda.com/free/miniconda/index.html) installed.
-   Clone the repo and enter its root folder

```shell
git clone git@github.com:tergite/tergite-calibration.git
cd tergite-calibration
```

- Create the conda environment

```shell
conda create -n tac python=3.8
```

-   Install dependencies

```shell
conda activate tac
pip install -e .
```

-   Run the CLI help command

```shell
acli --help
```

## Configuration

A number of configurations can be added to the tergite-calibration.
These include:

### - [`tergite_calibration/utils/user_input.py`](tergite_calibration/utils/user_input.py)

The sample-space for each node. 
The target node is also declared here.

### - [`tergite_calibration/config/device_config.toml`](tergite_calibration/config/device_config.toml)

A collection of reasonable initial values for the given device

### - [`dot-env-template.txt`](dot-env-template.txt)

Other parameters like the path to the Qblox Cluster configuration file (including IP address).

## Calibration Pipeline

Each calibration node goes through the following phases in order:

- compilation
- execution 
- post-processing
- redis updating

## Datasets

Datasets are stored in [`data_directory`](./data_directory)
They can be browsed with the dataset browser (coming soon)

## References

This document was adapted from [a gist by Brian A. Danielak](https://gist.github.com/briandk/3d2e8b3ec8daf5a27a62) which
was originally adapted from the open-source contribution guidelines
for [Facebook's Draft](https://github.com/facebook/draft-js/blob/a9316a723f9e918afde44dea68b5f9f39b7d9b00/CONTRIBUTING.md)

