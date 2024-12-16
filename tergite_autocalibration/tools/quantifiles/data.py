# BSD 2-Clause License
#
# Copyright (c) 2023, Damien Crielaard
# All rights reserved.

from __future__ import annotations

import dataclasses
import glob
import json
import os
from datetime import datetime

import logging

import xarray
from filelock import FileLock
from quantify_core.data.handling import (
    get_datadir,
    load_dataset,
    DATASET_NAME,
    locate_experiment_container,
)
from quantify_core.data.types import TUID
from quantify_core.measurement.control import _DATASET_LOCKS_DIR

logger = logging.getLogger(__name__)


class SplitTuid:
    """
    A class representing a split tuid.

    Attributes
    ----------
    _tuid : str
        The full tuid string.

    Methods
    -------
    date() -> str
        Returns the date portion of the tuid.
    time() -> str
        Returns the time portion of the tuid.
    name() -> str
        Returns the name portion of the tuid.
    tuid() -> str
        Returns the full tuid string.
    tuid(tuid: str)
        Sets the value of the full tuid string.
    """

    def __init__(self, full_tuid: str | TUID) -> None:
        """
        Parameters
        ----------
        full_tuid : str | TUID
            The full tuid string to split.
        """
        self._tuid = str(full_tuid)

    def __str__(self) -> str:
        """
        Returns
        -------
        str
            The full tuid string.
        """
        return self._tuid

    @property
    def date(self) -> str:
        """
        Returns
        -------
        str
            The date portion of the tuid.
        """
        return self._tuid[:8]

    @property
    def time(self) -> str:
        """
        Returns
        -------
        str
            The time portion of the tuid.
        """
        return self._tuid[9:15]

    @property
    def timestamp(self) -> datetime:
        """
        Returns
        -------
        datetime
            The timestamp of the tuid.
        """
        return datetime.strptime(self._tuid[0:15], "%Y%m%d-%H%M%S")

    @property
    def name(self) -> str:
        """
        Returns
        -------
        str
            The name portion of the tuid.
        """
        return self._tuid[27:]

    @property
    def tuid(self) -> str:
        """
        Returns
        -------
        str
            The full tuid string.
        """
        return self._tuid[:26]

    @property
    def full_tuid(self) -> str:
        """
        Returns
        -------
        str
            The full tuid string including name.
        """
        return self._tuid

    @full_tuid.setter
    def full_tuid(self, tuid: str) -> None:
        """
        Sets the value of the full tuid string.

        Parameters
        ----------
        tuid : str
            The new value for the full tuid string.
        """
        self._tuid = tuid


@dataclasses.dataclass
class DateResults:
    """
    A dataclass to store the results for a given date.
    """

    name: str
    """The name of the dataset."""
    date: str
    """The date of the dataset as string."""
    time: str
    """The time of the dataset as string."""
    keywords_: str
    """The keywords of the dataset as string."""


def get_results_for_date(date: datetime | None) -> dict[str, DateResults]:
    """
    Retrieves a dictionary of results for a given date.

    Parameters
    ----------
    date
        A datetime object representing the date to retrieve results for.

    Returns
    -------
        A dictionary of results, where each key is a TUID and each value is a DateResults object.
    """

    def get_kwds(tuid: SplitTuid) -> list[str] | list[tuple[str, str]]:
        """
        Retrieves keywords for a given TUID.

        Parameters
        ----------
        tuid
            A string representing the TUID to retrieve keywords for.

        Returns
        -------
            A list of keywords (as strings) if retrieval is successful, or a list with a single string element
            containing an error message if retrieval fails.
        """
        try:
            # Load dataset using TUID
            ds = safe_load_dataset(tuid.tuid)

            # Get x and y values from dataset coordinates and data variables
            x_vals = [val.long_name for val in list(ds.coords.values())]
            y_vals = [val.long_name for val in list(ds.data_vars.values())]

            # Combine x and y values into list of keywords
            return x_vals + y_vals
        except Exception as e:
            # If retrieval fails, return list with error message
            return [f"Error: {str(e)}"]

    # If date is None, return empty dictionary
    if date is None:
        return {}

    # Format date as string
    date_str = date.strftime("%Y%m%d")

    # Get path to directory for given date
    path = os.path.join(get_datadir(), date_str)

    # Raise error if path does not exist
    if not os.path.exists(path):
        raise ValueError(f"Path {path} does not exist")

    # Get list of subdirectories in path
    sub_dirs = os.listdir(path)

    # Get list of TUID names from subdirectories
    tuid_names = [
        SplitTuid(os.path.basename(sub_dir))
        for sub_dir in sub_dirs
        if os.path.isdir(os.path.join(path, sub_dir))
    ]

    # Get list of keywords for each TUID
    keywords = list(map(get_kwds, tuid_names))

    # Convert TUID names to datetime objects
    datetimes = []
    for tuid_name in tuid_names:
        try:
            datetimes.append(tuid_name.timestamp)
        except ValueError:
            # Ignore TUIDs that do not match the expected format
            tuid_names.remove(tuid_name)

    # Create dictionary of results, where each key is a TUID and each value is a DateResults object
    results = {
        TUID(tuid_name.tuid): DateResults(
            name=tuid_name.name,
            date=dt.strftime("%Y-%m-%d"),
            time=dt.strftime("%H:%M:%S"),
            keywords_=str(kwd),
        )
        for (tuid_name, dt, kwd) in zip(tuid_names, datetimes, keywords)
    }

    return results


def safe_load_dataset(tuid: str | TUID) -> xarray.Dataset:
    """
    Load a dataset in a safe manner.

    Parameters
    ----------
    tuid
        The tuid of the dataset to load.

    Returns
    -------
    xarray.Dataset
        The loaded dataset.
    """
    tuid = SplitTuid(tuid)
    lockfile = os.path.join(
        _DATASET_LOCKS_DIR, tuid.tuid + "-" + DATASET_NAME + ".lock"
    )
    with FileLock(lockfile, 5):
        logger.info(f"Loading dataset {tuid.full_tuid}.")
        ds = load_dataset(TUID(tuid.tuid))
    return ds


def get_all_dates_with_measurements() -> list[datetime]:
    """
    Get a list of all dates with measurements.

    Returns
    -------
    list[datetime]
        A list of all dates with measurements.
    """
    dirnames = glob.glob(os.path.join(get_datadir(), "*/"), recursive=False)

    dates = [os.path.basename(os.path.abspath(dirname))[:8] for dirname in dirnames]

    parsed_dates = []
    for date in dates:
        try:
            parsed_dates.append(datetime.strptime(date, "%Y%m%d"))
        except ValueError:  # discard dates that are not in the correct format
            pass

    return sorted(list(set(parsed_dates)), reverse=True)


def get_snapshot_as_dict(tuid: str | TUID) -> dict[str, any] | None:
    """
    Get a snapshot of a dataset as a dictionary.

    Parameters
    ----------
    tuid
        The tuid of the dataset to load.

    Returns
    -------
        The snapshot of the dataset. None if no snapshot is found.
    """
    exp_container = locate_experiment_container(tuid)
    snapshot_path = os.path.join(exp_container, "snapshot.json")
    if os.path.exists(snapshot_path):
        with open(snapshot_path, "r") as f:
            return json.load(f)
    return None
