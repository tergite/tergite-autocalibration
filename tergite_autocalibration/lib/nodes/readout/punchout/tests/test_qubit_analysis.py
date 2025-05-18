# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os
from pathlib import Path

import matplotlib
from matplotlib import pyplot as plt
import pytest
import xarray as xr
from numpy import ndarray

from tergite_autocalibration.lib.base.analysis import (
    BaseAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.lib.nodes.readout.punchout.analysis import (
    PunchoutQubitAnalysis,
)

from tergite_autocalibration.tests.utils.decorators import with_os_env


def test_CanCreate():
    a = PunchoutQubitAnalysis("name", ["redis_field"])
    assert isinstance(a, PunchoutQubitAnalysis)
    assert isinstance(a, BaseQubitAnalysis)
    assert isinstance(a, BaseAnalysis)


@pytest.fixture(autouse=False)
def setup_data():
    dataset_path = (
        Path(__file__).parent / "data" / "dataset_coupler_spectroscopy_0.hdf5"
    )
    ds = xr.open_dataset(dataset_path)

def amplitude_for_qubit(ds, qubit)    
    ds = xr.merge(ds[var] for var in ["yq06"])
    ds.attrs["qubit"] = qubit

    a = PunchoutQubitAnalysis("name", ["redis_fields"])
    qoi = a.setup_coupler_and_analyze(ds, qubit)
    return qoi["measure:pulse_amp"]

def test_amplitude_for_q06(
    setup_data: xr.Dataset,
):
    ds = setup_data
    amplitude = amplitude_for_qubit(ds, "q06")
    assert amplitude["q06"] == 0.016

def test_amplitude_for_q07(
    setup_data: xr.Dataset,
):
    ds = setup_data
    amplitude = amplitude_for_qubit(ds, "q07")
    assert amplitude["q06"] == 0.016

def test_amplitude_for_q10(
    setup_data: xr.Dataset,
):
    ds = setup_data
    amplitude = amplitude_for_qubit(ds, "q10")
    assert amplitude["q06"] == 0.045

def test_amplitude_for_q12(
    setup_data: xr.Dataset,
):
    ds = setup_data
    amplitude = amplitude_for_qubit(ds, "q12")
    assert amplitude["q06"] == 0.030

def test_amplitude_for_q15(
    setup_data: xr.Dataset,
):
    ds = setup_data
    amplitude = amplitude_for_qubit(ds, "q15")
    assert amplitude["q06"] == 0.060
