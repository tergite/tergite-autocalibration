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


def get_number_of_batches(samplespace: Dict[str, Dict[str, list[NDArray]]]):
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
            raise TypeError("samplespace does not contain batches")
    return number_of_batches


def get_batched_coord(samplespace: Dict[str, Dict[str, list[NDArray]]]) -> str:
    """
    if the samplespace is a list of NDarrays,
    return the name of the settable, e.g. 'frequencies'
    """
    for settable, qubit_dict in samplespace.items():
        qubit_dict = dict(qubit_dict)
        q = Array(qubit_dict)
        if isinstance(q.root, BatchedArray):
            batched_coord = settable
    return batched_coord


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
