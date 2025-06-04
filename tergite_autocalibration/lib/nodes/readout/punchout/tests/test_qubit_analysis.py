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

from pathlib import Path
import pytest
import xarray as xr
from tergite_autocalibration.lib.base.analysis import (
    BaseAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.lib.nodes.readout.punchout.analysis import (
    PunchoutQubitAnalysis,
)


def test_CanCreate():
    a = PunchoutQubitAnalysis("name", ["redis_field"])
    assert isinstance(a, PunchoutQubitAnalysis)
    assert isinstance(a, BaseQubitAnalysis)
    assert isinstance(a, BaseAnalysis)


@pytest.fixture(autouse=False)
def setup_data():
    dataset_path = Path(__file__).parent / "data" / "dataset_punchout_0.hdf5"
    ds = xr.open_dataset(dataset_path)
    return ds


def amplitude_for_qubit(ds, qubit):
    long_name = f"y{qubit}"
    ds = xr.merge(ds[var] for var in [long_name])
    ds.attrs["qubit"] = qubit

    a = PunchoutQubitAnalysis("name", ["measure:pulse_amp"])
    qoi = a.process_qubit(ds, qubit)
    return qoi.analysis_result["measure:pulse_amp"]["value"]


def test_amplitude_for_q06(setup_data: xr.Dataset):
    ds = setup_data
    amplitude = amplitude_for_qubit(ds, "q06")
    assert amplitude - 0.016 < 0.001


def test_amplitude_for_q07(setup_data: xr.Dataset):
    ds = setup_data
    amplitude = amplitude_for_qubit(ds, "q07")
    assert amplitude - 0.016 < 0.001


def test_amplitude_for_q10(setup_data: xr.Dataset):
    ds = setup_data
    amplitude = amplitude_for_qubit(ds, "q10")
    assert amplitude - 0.045 < 0.001


def test_amplitude_for_q12(setup_data: xr.Dataset):
    ds = setup_data
    amplitude = amplitude_for_qubit(ds, "q12")
    assert amplitude - 0.030 < 0.001


def test_amplitude_for_q15(setup_data: xr.Dataset):
    ds = setup_data
    amplitude = amplitude_for_qubit(ds, "q15")
    assert amplitude - 0.06 < 0.001
