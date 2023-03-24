from __future__ import annotations

import argparse

from quantifiles import version
from quantifiles.main import main

from pathlib import Path

__all__ = ["quantifiles", "__version__"]

__version__ = version.__version__

_static_reference = None


def quantifiles(data_dir: str | Path | None = None):
    global _static_reference

    if _static_reference is None:
        _static_reference = main(data_dir)

    return _static_reference


def entry_point():
    parser = argparse.ArgumentParser(
        description="Quantifiles - The quantify data browser."
    )
    parser.add_argument(
        "--datadir", default=None, help="Data directory to open the gui with."
    )
    args = parser.parse_args()

    quantifiles(args.datadir)


if __name__ == "__main__":
    entry_point()
