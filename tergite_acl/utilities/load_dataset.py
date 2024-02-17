import xarray as xr
from tergite_acl.utilities.root_path import data_directory
from os import walk

def extract_ds_date(filename:str) -> int:
    #TODO use datetime module for proper datetime handling
    ym, day, time, node, tuid = filename.split('-',4)
    date = int(ym + day + time)
    return date

def load_multiplexed_dataset(user_substr: str) -> xr.Dataset:
    _, _, filenames = next(walk((data_directory)))
    matched_list = list(filter(lambda x: user_substr in x, filenames))
    latest_file = max(matched_list, key=extract_ds_date)
    ds = xr.open_dataset(data_directory / latest_file)
    return ds
