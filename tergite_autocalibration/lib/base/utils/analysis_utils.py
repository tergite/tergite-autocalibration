# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou  2026
# (C) Chalmers Next Labs AB 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
import xarray as xr


def filter_ds_by_element(dataset: xr.Dataset, element: str):
    """
    Filters the dataset, by keeping only the data arrays
    and the corresponding coords that have
    their 'qubit' attribute equal to provided element.

    Parameters
    ----------
    dataset: xarray.Dataset
        the full initial dataset
     element: str
        the qubit or coupler of interest

    Returns
    -------
    xarray.Dataset
        the filtered dataset with data only for the filtered element

    """
    partial_ds = dataset.filter_by_attrs(element=element)
    partial_ds.attrs["qubit"] = element
    return partial_ds
