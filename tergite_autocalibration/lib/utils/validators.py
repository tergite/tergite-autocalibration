# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from typing import Dict, Union

from numpy._typing import NDArray
from pydantic import ConfigDict, RootModel


class SimpleSamplespace(RootModel):
    root: Dict[str, Dict[str, NDArray]]
    model_config = ConfigDict(arbitrary_types_allowed=True)


class MixedSamplespace(RootModel):
    root: Dict[str, Union[Dict[str, NDArray], Dict[str, list[NDArray]]]]
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Samplespace(RootModel):
    root: Union[
        SimpleSamplespace,
        MixedSamplespace,
    ]
    model_config = ConfigDict(arbitrary_types_allowed=True)


class BatchedArray(RootModel):
    root: Dict[str, list[NDArray]]
    model_config = ConfigDict(arbitrary_types_allowed=True)


class SimpleArray(RootModel):
    root: Dict[str, NDArray]
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Array(RootModel):
    root: Union[BatchedArray, SimpleArray]
    model_config = ConfigDict(arbitrary_types_allowed=True)


def get_number_of_batches(
    samplespace: Dict[str, Union[Dict[str, NDArray], Dict[str, list[NDArray]]]]
):
    """
    if the samplespace is a list of NDarrays,
    return the number of individual arrays per qubit
    """
    for qubit_dict in samplespace.values():
        qubit_dict = dict(qubit_dict)
        q = Array(qubit_dict)
        if isinstance(q.root, BatchedArray):
            for element, samples in qubit_dict.items():
                number_of_batches = len(samples)
        else:
            number_of_batches = 1
    return number_of_batches


def get_batched_dimensions(
    samplespace: Dict[str, Dict[str, list[NDArray]]]
) -> list[str]:
    """
    if the samplespace is a list of NDarrays,
    return the name of the settable, e.g. 'frequencies'
    """
    batched_dimensions = []
    for settable, qubit_dict in samplespace.items():
        qubit_dict = dict(qubit_dict)
        q = Array(qubit_dict)
        if isinstance(q.root, BatchedArray):
            for qubit in qubit_dict:
                batched_dimensions.append(str(settable) + str(qubit))

    return batched_dimensions


def reduce_batch(samplespace, batch: int):
    """
    if the samplespace is a list of NDarrays,
    keep only the array of index=batch. the reduced samplespace
    has the same structure as a regular samplespace.
    """
    reduced_samplespace = {}
    for settable, qubit_dict in samplespace.items():
        qubit_dict = dict(qubit_dict)
        q = Array(qubit_dict)
        if isinstance(q.root, SimpleArray):
            reduced_samplespace[settable] = qubit_dict
        elif isinstance(q.root, BatchedArray):
            reduced_samplespace[settable] = {}
            for element, samples in qubit_dict.items():
                reduced_samplespace[settable][element] = samples[batch]
    return reduced_samplespace
