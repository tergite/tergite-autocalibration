from os import walk

import xarray as xr

from tergite_autocalibration.config.settings import DATA_DIR


def extract_ds_date(filename: str) -> int:
    # TODO use datetime module for proper datetime handling
    ym, day, time, node, tuid = filename.split('-', 4)
    date = int(ym + day + time)
    return date


def load_multiplexed_dataset(user_substr: str) -> xr.Dataset:
    _, _, filenames = next(walk(DATA_DIR))
    matched_list = list(filter(lambda x: user_substr in x, filenames))
    latest_file = max(matched_list, key=extract_ds_date)
    ds = xr.open_dataset(DATA_DIR / latest_file)
    return ds
