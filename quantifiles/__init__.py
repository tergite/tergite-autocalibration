from __future__ import annotations

import argparse
import logging

from quantifiles.main import main

from pathlib import Path

__all__ = ["quantifiles", "__version__"]

__version__ = "0.1.0"


def quantifiles(
    data_dir: str | Path | None = None,
    liveplotting: bool = False,
    log_level: int | str = logging.WARNING,
) -> None:
    """
    Entry point for the quantifiles from python.

    Parameters
    ----------
    data_dir
        The data directory to open the gui with.
    liveplotting
        Whether to automatically open plots for new measurements.
    log_level
        The level to configure the logger to.

    Returns
    -------
    None
    """
    main(data_dir, liveplotting, log_level)


def entry_point():
    """
    Entry point for the quantifiles command line interface.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(
        description="Quantifiles - The quantify data browser."
    )
    parser.add_argument(
        "--datadir", default=None, help="Data directory to open the gui with."
    )
    parser.add_argument(
        "--liveplotting", action="store_true", help="enable live plotting"
    )
    parser.add_argument(
        "--log_level", default="WARNING", help="The level to configure the logger to."
    )
    args = parser.parse_args()

    quantifiles(args.datadir, args.liveplotting, args.log_level)


if __name__ == "__main__":
    entry_point()
