# BSD 2-Clause License
#
# Copyright (c) 2023, Damien Crielaard
# All rights reserved.

from __future__ import annotations

import dataclasses
import glob
import json
import os
import re
from datetime import datetime

import xarray
from filelock import FileLock
from quantify_core.data.handling import (
    get_datadir,
    load_dataset,
    DATASET_NAME,
    locate_experiment_container,
    load_dataset_from_path,
)
from quantify_core.data.types import TUID
from quantify_core.measurement.control import _DATASET_LOCKS_DIR

from tergite_autocalibration.utils.logging import logger

# This maps all dataset ids to the respective path.
# Since our logging structure is incompatible with the format given by quantify,
# we have an alternative function to locate the file path.
# Implementing it with a map, makes the whole process faster, because we can store
# already known paths and do not have to crawl for them in the datadir again.
# Example:
#   {20250109-113613-466-2727b9-resonator_spectroscopy:
#       DATA_DIR/date/run/20250109-113613-466-2727b9-resonator_spectroscopy,
#    20250109-113634-547-474d6c-qubit_01_spectroscopy:
#       DATA_DIR/date/run/20250109-113634-547-474d6c-qubit_01_spectroscopy}
_TUID_PATH_MAP = {}


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
    # TODO: This function has to use maybe the path instead of the date?

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
    date_str = date.strftime("%Y-%m-%d")

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


def get_runs_by_date(date: datetime | None) -> list[tuple[datetime, str]]:
    """
    Retrieve a tuple of runs with time and status for a given date.
    This is to create the e.g. a table (QTreeWidget) for the run selection.

    Args:
        date: The date to retrieve runs for

    Returns:
        A list of tuples containing the run time and the status of that run.

    """
    if date is None:
        return []

    # Read the date part to construct the base folder
    date_str = date.strftime("%Y-%m-%d")
    path = os.path.join(get_datadir(), date_str)

    # Iterate over the subdirectories inside the date folder
    run_results = []
    for run_dir_ in os.listdir(path):

        # Use regex to capture the first and second parts
        # Strings look like e.g. "2025-01-09_SUCCESS-ro_amplitude_two_state_optimization"
        match = re.match(r"([0-9\-]+)_([A-Z]+)", run_dir_)

        if match:
            # Construct the time object from the folder name
            time_obj_ = datetime.strptime(match.group(1), "%H-%M-%S").time()
            run_timestamp_ = date.replace(
                hour=time_obj_.hour, minute=time_obj_.minute, second=time_obj_.second
            )

            # Add status and timestamp to the results
            status_ = match.group(2)
            run_results.append((run_timestamp_, status_))

    return run_results


def get_results_for_run(date: datetime | None) -> dict[str, DateResults]:
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
    date_str = date.strftime("%Y-%m-%d")

    # Get path to directory for given date
    path_prefix = os.path.join(get_datadir(), date_str)

    # Get path to the run folder
    run_time = date.strftime("%H-%M-%S")
    run_folder = [
        os.path.basename(d)
        for d in glob.glob(f"{path_prefix}/*{run_time}*")
        if os.path.isdir(d)
    ][0]
    path = os.path.join(path_prefix, run_folder)

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


def _update_tuid_map():
    """
    This is crawling for all tuid paths in the data directory and updates the cache.
    """
    pass

def _locate_dataset_path(tuid: str | TUID) -> str:
    """
    This crawls the data directory for the experiment results with the given TUID.

    Args:
        tuid: quantify TUID for the dataset.

    Returns:
        Path to the dataset as string.

    """

    # If the TUID is already cached, we can just return it
    if tuid in _TUID_PATH_MAP.keys():
        return _TUID_PATH_MAP[tuid]

    # Otherwise, we crawl and check whether it can be loaded.
    else:
        pass


def safe_load_dataset_from_path(tuid: str | TUID) -> xarray.Dataset:
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
        ds = load_dataset_from_path(_locate_dataset_path(TUID(tuid.tuid)))
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

    parsed_dates = []
    for dirname in dirnames:
        try:
            date_ = os.path.abspath(dirname)[-10:]
            extracted_date = datetime.strptime(date_, "%Y-%m-%d")
            parsed_dates.append(extracted_date)
        except (
            ValueError
        ):  # Discard dates that are not in the correct format and cannot be extracted
            pass
        except (
            KeyError
        ):  # Discard situations where the path cannot be parsed because it is too short
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
