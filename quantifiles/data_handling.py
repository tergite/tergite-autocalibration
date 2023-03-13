from __future__ import annotations

import dataclasses
import glob
import os
from datetime import datetime

import logging

from filelock import FileLock
from quantify_core.data.handling import get_datadir, load_dataset, DATASET_NAME
from quantify_core.data.types import TUID
from quantify_core.measurement.control import _DATASET_LOCKS_DIR

logger = logging.getLogger(__name__)


def _get_all_dataset_paths():
    return glob.glob(os.path.join(get_datadir(), "**/*.hdf5"), recursive=True)


def _get_all_tuids():
    paths = _get_all_dataset_paths()
    dirnames = [os.path.dirname(path) for path in paths]
    return {os.path.basename(dirname) for dirname in dirnames}


@dataclasses.dataclass
class DateResults:
    name: str
    date: str
    time: str
    keywords_: str


def get_results_for_date(date: datetime | None) -> dict[str, DateResults]:
    def get_kwds(tuid: str):
        try:
            ds = safe_load_dataset(TUID(tuid[:26]))
            x_vals = [val.long_name for val in list(ds.coords.values())]
            y_vals = [val.long_name for val in list(ds.data_vars.values())]
            return x_vals + y_vals
        except Exception as e:
            return [str(e)]

    if date is None:
        return {}

    date_str = date.strftime("%Y%m%d")
    path = os.path.join(get_datadir(), date_str)
    if not os.path.exists(path):
        raise ValueError(f"Path {path} does not exist")

    sub_dirs = os.listdir(path)
    tuid_names = [
        os.path.basename(sub_dir)
        for sub_dir in sub_dirs
        if os.path.isdir(os.path.join(path, sub_dir))
    ]

    keywords = list(map(get_kwds, tuid_names))

    datetimes = [
        datetime.strptime(tuid_name[:15], "%Y%m%d-%H%M%S") for tuid_name in tuid_names
    ]

    results = {
        TUID(tuid_name[:26]): DateResults(
            name=tuid_name[27:],
            date=dt.strftime("%Y-%m-%d"),
            time=dt.strftime("%H:%M:%S"),
            keywords_=str(kwd),
        )
        for idx, (tuid_name, dt, kwd) in enumerate(zip(tuid_names, datetimes, keywords))
    }
    return results


def safe_load_dataset(tuid: str):
    tuid = tuid[:26]
    lockfile = os.path.join(
        _DATASET_LOCKS_DIR, tuid + "-" + DATASET_NAME + ".lock"
    )
    with FileLock(lockfile, 5):
        logger.info(f"Loading dataset {tuid}.")
        ds = load_dataset(TUID(tuid))
    return ds


def get_all_dates_with_measurements():
    paths = _get_all_dataset_paths()

    dirnames = [os.path.dirname(path) for path in paths]

    dates = [os.path.basename(dirname)[:8] for dirname in dirnames]

    parsed_dates = []
    for date in dates:
        try:
            parsed_dates.append(datetime.strptime(date, "%Y%m%d"))
        except ValueError:  # discard dates that are not in the correct format
            pass

    return sorted(list(set(parsed_dates)), reverse=True)

