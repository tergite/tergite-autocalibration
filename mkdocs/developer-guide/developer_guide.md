# Developer Guide

This and the following sections provide information on how to develop code in tergite-autocalibration.

## Additional installations

Consider installing Quarto and other packages before you create your coda environment to have the path correctly
initialised in your environment.
This is not necessary, but it can simplify operations later, especially using VSCode.

After you install tergite-autocalibration with:

```bash
pip install -e ".[test,dev]"
```

this will install the additional packages for developing code and running tests

## Naming convention and style

We use American English, please set any spell checker to this language.

- The file names should be written using `snake_case`, with words written in lowercase and separated by underscores.
- Class names should be in `PascalCase` (where all words are capitalized). Many class do not follow this rule and use
  CamelCase with underscore, they will be changed.
- Methods should be in `snake_case`
- Variables should be in `snake_case`
- We follow [PEP8](https://peps.python.org/pep-0008/) as the coding style guide.
- Docstrings should use the [Google format](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings). See example below:

```python
def divide_numbers(numerator: float, denominator: float) -> float:
    """
    Divides two numbers and returns the result.

    Args:
        numerator (float): The number to be divided.
        denominator (float): The number by which the numerator is divided.

    Returns:
        float: The result of the division.

    Raises:
        ValueError: If the denominator is zero.

    Note:
        This function does not handle complex numbers.

    Example:
        >>> divide_numbers(10, 2)
        5.0
        >>> divide_numbers(5, 0)
        Traceback (most recent call last):
            ...
        ValueError: Denominator cannot be zero.
    """
    if denominator == 0:
        raise ValueError("Denominator cannot be zero.")
    return numerator / denominator
```

## IDE preloaded settings

There are settings available in the repo for IDEs, recommending extensions and settings.
Please discuss with the team before modifying these default settings, they should be changed only with the consensus of
the team.

### VSCode

Black is a recommended python extension.
Some settings are recommended too.
You can find the settings for VSCode in the repository in the folder `.vscode`.

## Things to do before a commit

Please read carefully below, what should be done before doing a commit to a merge request.
Most of the points are going to be checked automatically in GitLab, so, you would receive an error when running the
pipeline.

### Commit message

When submitting contributions, please prepend your commit messages with:

- `fix:` for bug fixes
- `feat:` for introducing and working on a new feature (e.g. a new measurement node or a new analysis class)
- `chore:` for refactoring changes or any change that doesn't affect the functionality of the code
- `docs:` for changes in the README, docstrings etc
- `test:` or `dev:` for testing or development changes (e.g. profiling scripts)

### Copyright statement

When you create or modify a file, make sure that add the following copyright text is present at the top of the file.
Remember to add your name and do not delete previous contributors. If you add the statement to a file that does not have
one, please check on git the names of contributors.

```python
# This code is part of Tergite Autocalibration
#
# (C) Copyright WRITE YOUR NAME HERE, 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
``` 

### Changelog

Update the changelog in the section called [Unreleased]. Please note that there are several sections titled "Added", "
Change" and "Fixed"; place your text in the correct category.

### Static code analyzer

The code analyzer used in the project is black, which is installed as part of the dev dependencies.
To use black, open a shell and run

```bash
black .
```

Please make sure to run it before committing to a merge request.

If your pipeline is still showing an error when you are running black, please make sure that you have installed the
right version of black.
You can check that by running

```bash
black --version
```

If your black version differs, it might be possible that you have had installed a version of black either in your base
environment or via apt.
To remove these versions, please deactivate your conda environment with `conda deactivate` and then run:

```bash
sudo apt remote black
```

or

```bash
pip uninstall black
```

Next, please activate again your Python environment and install the correct version black as defined in
the `pyproject.toml` file.

```bash
pip install black==VERSION_FROM_PYPROJECT_TOML
```

## Next steps:

As you noticed, most of the above advice contains the formatting and other formal steps during development.
Consider reading about:

- [Unit testing](unit_tests.md) to find out more about how to write test cases for the code.
- [Nodes](new_node_creation.md) on how to create a new calibration node.
- [Node Classes](node_classes.md) to learn about the different types of nodes that the framework
  supports.

If you are having any feedback about the documentation or want to work on documentation, please continue with this
developer guide about [how to contribute with documentation](writing_documentation.md).