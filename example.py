from numpy import array
import xarray as xr
from example_ds import ex

ds = xr.Dataset.from_dict(ex)
print(ds)

#---

print( ds.y0)
print( )
print( ds.y0.values)
print( )
print( )
print( )
print( )

print( dir(ds.y0.coords ))
vals =  ds.y0.coords.values()

#---
print( len(ds.coords))
#---
ds_0 = ds.y0.to_dataset()
# rkey =  list(ds.y0.coords.keys())[0]
# print( ds[rkey].values )
print( list(ds_0.data_vars.keys()))
print( ds_0.y0.attrs)

#---
for var in ds.data_vars:
    print( ds[var].attrs['qubit'])
