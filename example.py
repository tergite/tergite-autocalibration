import xarray as xr
from example_ds import ex_dict

ds = xr.Dataset.from_dict(ex_dict)
print(ds)
print(ds.y0.f)
