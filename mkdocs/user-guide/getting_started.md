# Getting started

This guide contains some information on how to get started with the automatic calibration.
Please consider also reading the `README.md` file in the git repository for more information.

## Prerequisites

The automatic calibration requires `redis` for on-memory data storage.
As redis operates only on Linux systems, the calibration has to run either on one of:

- Linux distributions
- WSL (Windows Subsystem for Linux) environments, installed on a Windows system.
  WSL requires **Windows 10** and a version of at least **1903**.

Installation instructions for redis can be found
here: https://redis.io/docs/getting-started/installation/install-redis-on-linux/

The link for the redis installation also contains instructions on how to start a redis instance.
However, if you already have redis installed, you can run it using:

```bash
redis-server --port YOUR_REDIS_PORT
```

Usually, redis will run automatically on port `6379`, but in a shared environment please check with others to get your
redis port, since you would overwrite each other's memory.

## Installation

The first step during the installation is to clone the repository.
Please note that the link below is the link to the public mirror of the repository on GitHub.
If you are developing code, most likely, you have to replace it with the link to the development server.

```bash
git clone git@github.com:tergite/tergite-autocalibration.git
```

To manage Python packages, we are using the package manager `conda`.
It is recommended to create an environment for your project - alternatively, you can also just use Python 3.12

```bash
conda create -n tac python=3.12 -y
```

Here, `tac` stands for tergite-autocalibration.
We can activate and use the environment like this:

```bash
conda activate tac
```

If you are not using conda, activate the environment with:

```bash
source activate tac
```

Now, you should enter the repository folder, because the following commands have to be executed in there.

```bash
cd tergite-autocalibration
```

To install the repository in editable mode.
In Python the editable mode is triggerd by the parameter `-e`.
This means that when you changed and saved your code files, they will be automatically loaded into the environment
without re-installation.

```bash
pip install -e .
```

Here `.` is the root directory (i.e. the directory that contains the `pyproject.toml` file)

### Next steps:

- [Configuration files](configuration_files.md) in case you are interested on how to configure the
  application and run the first experiments.
- [Developer guide](../developer-guide/developer_guide.md) in case you would like to start developing features for the automatic
  calibration.