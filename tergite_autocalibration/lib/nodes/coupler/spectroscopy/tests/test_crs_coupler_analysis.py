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
    BaseCouplerAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.spectroscopy.analysis import (
    CouplerResonatorSpectroscopyAnalysis,
)

from tergite_autocalibration.tests.utils.decorators import with_os_env


def test_CanCreate():
    a = CouplerResonatorSpectroscopyAnalysis("name", ["redis_field"])
    assert isinstance(a, CouplerResonatorSpectroscopyAnalysis)
    assert isinstance(a, BaseCouplerAnalysis)
    assert isinstance(a, BaseAnalysis)


@pytest.fixture(autouse=False)
def setup_q06_q07_data():
    dataset_path = (
        Path(__file__).parent / "data" / "dataset_coupler_spectroscopy_0.hdf5"
    )
    ds = xr.open_dataset(dataset_path)
    coupler = "q06_q07"
    ds = xr.merge(ds[var] for var in ["yq06", "yq07"])
    ds.attrs["coupler"] = coupler
    return ds, coupler


def test_get_crossings_for_q06_q07(
    setup_q06_q07_data: tuple[xr.Dataset, str, ndarray, ndarray],
):
    ds, coupler = setup_q06_q07_data
    a = CouplerResonatorSpectroscopyAnalysis("name", ["redis_fields"])
    qoi = a.setup_coupler_and_analyze(ds, coupler)

    crossings = qoi["qubit_crossing_points"]
    assert crossings["q06"] == pytest.approx([-0.000425, 0.000675], abs=1e-6)
    assert crossings["q07"] == pytest.approx([-0.00025, 0.000525], abs=1e-6)


@pytest.fixture(autouse=False)
def setup_q08_q09_data():
    dataset_path = (
        Path(__file__).parent / "data" / "dataset_coupler_spectroscopy_0.hdf5"
    )
    ds = xr.open_dataset(dataset_path)
    coupler = "q08_q09"
    ds = xr.merge(ds[var] for var in ["yq08", "yq09"])
    ds.attrs["coupler"] = coupler
    return ds, coupler


def test_get_crossings_for_q08_q09(
    setup_q08_q09_data: tuple[xr.Dataset, str, ndarray, ndarray],
):
    ds, coupler = setup_q08_q09_data
    a = CouplerResonatorSpectroscopyAnalysis("name", ["redis_fields"])
    qoi = a.setup_coupler_and_analyze(ds, coupler)

    crossings = qoi["qubit_crossing_points"]
    assert crossings["q08"] == pytest.approx([-0.0008, 0.00075], abs=1e-6)
    assert crossings["q09"] == pytest.approx([0], abs=1e-6)


@pytest.fixture(autouse=False)
def setup_q12_q13_data():
    dataset_path = (
        Path(__file__).parent / "data" / "dataset_coupler_spectroscopy_0.hdf5"
    )
    ds = xr.open_dataset(dataset_path)
    coupler = "q12_q13"
    ds = xr.merge(ds[var] for var in ["yq12", "yq13"])
    ds.attrs["coupler"] = coupler
    return ds, coupler


def test_get_crossings_for_q12_q13(
    setup_q12_q13_data: tuple[xr.Dataset, str, ndarray, ndarray],
):
    ds, coupler = setup_q12_q13_data
    a = CouplerResonatorSpectroscopyAnalysis("name", ["redis_fields"])
    qoi = a.setup_coupler_and_analyze(ds, coupler)

    crossings = qoi["qubit_crossing_points"]
    assert crossings["q12"] == pytest.approx([-0.000425, 0.000825], abs=1e-6)
    assert crossings["q13"] == pytest.approx([0.0002], abs=1e-6)


@pytest.fixture(autouse=False)
def setup_q14_q15_data():
    dataset_path = (
        Path(__file__).parent / "data" / "dataset_coupler_spectroscopy_0.hdf5"
    )
    ds = xr.open_dataset(dataset_path)
    coupler = "_q14_q15"
    ds = xr.merge(ds[var] for var in ["yq14", "yq15"])
    ds.attrs["coupler"] = coupler
    return ds, coupler


def test_get_crossings_for_q14_q15(
    setup_q14_q15_data: tuple[xr.Dataset, str, ndarray, ndarray],
):
    ds, coupler = setup_q14_q15_data
    a = CouplerResonatorSpectroscopyAnalysis("name", ["redis_fields"])
    qoi = a.setup_coupler_and_analyze(ds, coupler)

    crossings = qoi["qubit_crossing_points"]
    assert crossings["q14"] == pytest.approx([-0.00025, 0.000925], abs=1e-6)
    assert crossings["q15"] == pytest.approx([0.00025], abs=1e-6)


@with_os_env({"DATA_DIR": str(Path(__file__).parent / "results")})
def test_coupler_plot_is_created(setup_q06_q07_data):
    matplotlib.use("Agg")
    ds, coupler = setup_q06_q07_data
    a = CouplerResonatorSpectroscopyAnalysis("name", ["redis_fields"])
    a.setup_coupler_and_analyze(ds, coupler)

    figure_path = os.environ["DATA_DIR"] + "/Coupler_Spectroscopy.png"
    # Remove the file if it already exists
    if os.path.exists(figure_path):
        os.remove(figure_path)

    fig, ax = plt.subplots(figsize=(15, 7), ncols=2)
    plt.Axes
    a.plotter(ax[0], ax[1])
    fig.savefig(figure_path)
    plt.close()

    assert os.path.exists(figure_path)
    from PIL import Image

    with Image.open(figure_path) as img:
        assert img.format == "PNG", "File should be a PNG image"


@with_os_env({"DATA_DIR": str(Path(__file__).parent / "results")})
def test_qubit_spectroscopies_for_coupler_are_created(setup_q06_q07_data):
    matplotlib.use("Agg")
    ds, coupler = setup_q06_q07_data
    a = CouplerResonatorSpectroscopyAnalysis("name", ["redis_fields"])
    a.setup_coupler_and_analyze(ds, coupler)

    path = Path(os.environ["DATA_DIR"])
    a.plot_spectroscopies(path)

    figure_1_path = (
        os.environ["DATA_DIR"]
        + "/coupler_resonator_spectroscopy_q06_q07_q06_spectroscopies.png"
    )
    assert os.path.exists(figure_1_path)
    from PIL import Image

    with Image.open(figure_1_path) as img:
        assert img.format == "PNG", "File should be a PNG image"

    figure_2_path = (
        os.environ["DATA_DIR"]
        + "/coupler_resonator_spectroscopy_q06_q07_q07_spectroscopies.png"
    )
    assert os.path.exists(figure_2_path)
    from PIL import Image

    with Image.open(figure_2_path) as img:
        assert img.format == "PNG", "File should be a PNG image"
