# Contributing to tergite-autocalibration

**This project is currently not accepting pull requests from the general public yet.**

**It is currently being developed by the core developers only.**

[Chalmers Next Labs AB (CNL)](https://chalmersnextlabs.se) manages and maintains this project on behalf of all contributors.

## General information about contributions

Tergite is developed on a separate version control system and mirrored on GitHub.
If you are reading this on GitHub, then you are looking at a mirror. 

The following subsections are only relevant for people that are onboarded on the internal version control system.

### Contribute by using merge requests

Merge requests are the best way to propose changes to the codebase. We use a pattern similar to the
[GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow) and actively welcome your merge
requests.

1. Clone the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation. Read the section below on documentation.
4. Ensure the test suite passes. Run: `pytest tergite_autocalibration`
5. Make sure your code lints. This can be done by running: `black tergite_autocalibration --check`
6. Create the merge request!

### Issues and bug reports

Good bug reports can make it way easier for a developer to solve the issue.
A good bug report tends to contain:

- A quick summary and/or background
- Provide steps to reproduce the error
    - Be specific!
    - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

Here is [one example](http://stackoverflow.com/q/12488905/180626)
and [another example](http://www.openradar.me/11905408) on how to write a good bug report.

### Versioning

When versioning we follow the format `{year}.{month}.{patch_number}` e.g. `2023.12.0`.
Please find out more about versioning in the [change log](./CHANGELOG.md).

### Contact information

Since the GitHub repositories are only mirrors, no GitHub pull requests or GitHub issue/bug reports
are looked at. Please get in touch via
email [contact@quantum.chalmersnextlabs.se](mailto://contact@quantum.chalmersnextlabs.se) instead.

## How to develop

Make sure you have [conda](https://docs.anaconda.com/free/miniconda/index.html) installed.
Alternatively, you could also simply have [Python 3.10](https://www.python.org/downloads/) installed.
Clone the repo and enter its root folder:

```bash
git clone git@github.com:tergite/tergite-autocalibration.git
cd tergite-autocalibration
```

Create the conda environment

```bash
conda create -n tac python=3.10 -y
```

Install dependencies

```bash
conda activate tac
pip install -e .
```

Install the development and test dependencies

```bash
pip install poetry
poetry install --with dev,test
```

Run the CLI help command to see whether the application is running.

```bash
acli --help
```

You can find more information about the configuration files in the documentation.

### Testing

Tests require a redis instance running on port 6378.

```bash
redis-server --port 6378 {--daemonize yes}
```

Optionally, add `--daemonize yes` to run the redis instance in the background.
If it does not run on your user, try running it again with `sudo` rights.

Run the pytests for the whole application.

```bash
pytest tergite_autocalibration
```

You can find more information about unit tests in the documentation.

### Calibration Pipeline

Each calibration node goes through the following phases in order:

- compilation
- execution 
- post-processing
- redis updating

### Datasets

Datasets are stored in [`out`](./out).
They can be browsed with the dataset browser:
```
acli browser --datadir PATH_TO_DATA_DIRECTORY
```

### Documentation

Documentation is rendered with [Quarto](https://quarto.org/).
If you had quarto installed in the previous step you can enter the `docs_editable` folder and edit the markdown files.

```bash
cd docs_editable
```

Render the documentation and show a preview in the browser

```bash
quarto preview
```

Now you can edit the files in `docs_editable` and the contents in the browser window would update automatically.
If you just want to see the documentation, please open [`docs/index.html`](./docs/index.html) with your browser.
One of the documentation pages is also
about [how to write better documentation](./docs/developer-guide/writing_documentation.html).

### Installation of proprietary resources (optional, not recommended)
We do not recommend to make your code having dependencies to proprietary software.
If you still need to install proprietary dependencies, please do so by running:
```
pip install -r requirements_proprietary.txt
```
Make sure you have ssh access to all proprietary repositories, otherwise the installation will fail.

When you are using imports of proprietary resources in the code, please make sure that they are wrapped with a `try` and `catch` statement.
```
try:
    from superconducting_qubit_tools.clifford_module.randomized_benchmarking import *
except ImportError:
    logger.warning(
        "Could not find package: superconducting-qubit-tools.",
        "This is a proprietary licenced software.",
        "Please make sure that you are having a correct licence and install the dependency",
    )
```
Please try to use proprietary resources only on experimental features and do not integrate them into the default workflows.
The scope of the Tergite project is to be as open-source as possible.

## License

When you submit code changes, your submissions are understood to be under the
same [Apache 2.0 License](./LICENSE.txt) that covers the project. Feel free to contact the maintainers if that's a
concern.

### Contributor License Agreement

Before you can submit any code, all contributors must sign a
contributor license agreement (CLA). By signing a CLA, you're attesting
that you are the author of the contribution, and that you're freely
contributing it under the terms of the Apache-2.0 license.

The [individual CLA](https://tergite.github.io/contributing/icla.pdf) document is available for review as a PDF.

Please note that if your contribution is part of your employment or
your contribution is the property of your employer,
you will also most likely need to sign a [corporate CLA](https://tergite.github.io/contributing/ccla.pdf).

All signed CLAs are send by email
to [contact@quantum.chalmersnextlabs.se](mailto://contact@quantum.chalmersnextlabs.se).


## References

This document was adapted from [a gist by Brian A. Danielak](https://gist.github.com/briandk/3d2e8b3ec8daf5a27a62) which
was originally adapted from the open-source contribution guidelines
for [Facebook's Draft](https://github.com/facebook/draft-js/blob/a9316a723f9e918afde44dea68b5f9f39b7d9b00/CONTRIBUTING.md)

