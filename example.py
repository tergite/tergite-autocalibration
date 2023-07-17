from numpy import array
import xarray as xr
from example_ds import ex
import numpy as np

ds = xr.Dataset.from_dict(ex)
print(ds)

#---
# ds_0 = ds.y0.to_dataset()
# # rkey =  list(ds.y0.coords.keys())[0]
# # print( ds[rkey].values )
# print( list(ds_0.data_vars.keys()))
# print( ds_0.y0.attrs)

#---
# for var in ds.data_vars:
#     print( ds[var].attrs['qubit'])

#---

ds0 = xr.Dataset(coords={
    'y': ('y', list(range(5))),
    'x': ('x', list(range(3)))
    })

vals = np.array(list(range(15))).reshape(3,5)
print(f'{ vals = }')

ds0['v0'] = (('x','y'), vals)
print(f'{ ds0.v0.shape = }')


