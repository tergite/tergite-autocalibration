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
    QubitSpectroscopyVsCurrentCouplerAnalysis,
    ResonatorSpectroscopyVsCurrentCouplerAnalysis,
)
from tergite_autocalibration.utils.dto.qoi import QOI
from tergite_autocalibration.tests.utils.decorators import with_os_env
from tergite_autocalibration.lib.utils.redis import update_redis_trusted_values


def test_CanCreate():
    a = QubitSpectroscopyVsCurrentCouplerAnalysis("name", ["redis_field"])
    assert isinstance(a, QubitSpectroscopyVsCurrentCouplerAnalysis)
    assert isinstance(a, BaseCouplerAnalysis)
    assert isinstance(a, BaseAnalysis)


@pytest.fixture(autouse=False)
def setup_q06_q07_data():
    coupler = "q06_q07"
    ds_qu, ds_res = get_dataset_for_coupler(coupler)
    return ds_res, ds_qu, coupler

def get_dataset_for_coupler(coupler):
    qubits = coupler.split("_")
    dataset_path = (
        Path(__file__).parent / "data" / "dataset_coupler_spectroscopy_0.hdf5"
    )
    ds_qu = xr.open_dataset(dataset_path)
    ds_qu = xr.merge(ds_qu[var] for var in [f"y{qubits[0]}", f"y{qubits[1]}"])
    ds_qu.attrs["coupler"] = coupler

    dataset_path = (
        Path(__file__).parent / "data" / "dataset_coupler_resonator_spectroscopy_0.hdf5"
    )
    ds_res = xr.open_dataset(dataset_path)
    ds_res = xr.merge(ds_res[var] for var in [f"y{qubits[0]}", f"y{qubits[1]}"])
    ds_res.attrs["coupler"] = coupler
    return ds_qu,ds_res


def getCrossingForQubit(qoi: QOI, qubit: str = "q06"):
    results = qoi.analysis_result
    crossings: str = results[qubit]["crossing_points"]
    crossings = crossings.replace("np.float64", "float")
    crossings = eval(crossings)
    return crossings


def test_get_crossings_for_q06_q07(
    setup_q06_q07_data: tuple[xr.Dataset, str, ndarray, ndarray],
):
    ds_res, ds_qu, coupler = setup_q06_q07_data
    a = ResonatorSpectroscopyVsCurrentCouplerAnalysis(
        "resonator_spectroscopy_vs_current", ["resonator_crossing_points"]
    )
    qoi = a.process_coupler(ds_res, coupler)
    update_redis_trusted_values(
        "resonator_spectroscopy_vs_current", coupler, qoi, ["resonator_crossing_points"]
    )

    b = QubitSpectroscopyVsCurrentCouplerAnalysis("name", ["crossing_points"])
    qoi = b.process_coupler(ds_qu, coupler)

    q06_crossings = getCrossingForQubit(qoi, "q06")
    q07_crossings = getCrossingForQubit(qoi, "q07")
    print(q07_crossings)
    assert q06_crossings == pytest.approx(
        [-0.001925, -0.0011, 0.001375, 0.0022], abs=1e-6
    )
    assert q07_crossings == pytest.approx(
        [-0.002025, -0.001, 0.00128, 0.0023],
        abs=1e-6,
    )


@pytest.fixture(autouse=False)
def setup_q08_q09_data():
    coupler = "q08_q09"
    ds_qu, ds_res = get_dataset_for_coupler(coupler)
    return ds_res, ds_qu, coupler


def test_get_crossings_for_q08_q09(
    setup_q08_q09_data: tuple[xr.Dataset, str, ndarray, ndarray],
):
    ds_res, ds_qu, coupler = setup_q08_q09_data
    a = ResonatorSpectroscopyVsCurrentCouplerAnalysis(
        "resonator_spectroscopy_vs_current", ["resonator_crossing_points"]
    )
    qoi = a.process_coupler(ds_res, coupler)
    update_redis_trusted_values(
        "resonator_spectroscopy_vs_current", coupler, qoi, ["resonator_crossing_points"]
    )

    b = QubitSpectroscopyVsCurrentCouplerAnalysis("name", ["crossing_points"])
    qoi = b.process_coupler(ds_qu, coupler)

    q08_crossings = getCrossingForQubit(qoi, "q09")
    q09_crossings = getCrossingForQubit(qoi, "q08")
    assert q08_crossings == pytest.approx(
        [-0.00215, -0.00135, 0.001325, 0.002108], abs=1e-6
    )
    assert q09_crossings == pytest.approx(
        [-0.0023357, -0.001165, 0.0011375, 0.002275],
        abs=1e-6,
    )


@pytest.fixture(autouse=False)
def setup_q12_q13_data():
    coupler = "q12_q13"
    ds_qu, ds_res = get_dataset_for_coupler(coupler)
    return ds_res, ds_qu, coupler


def test_get_crossings_for_q12_q13(
    setup_q12_q13_data: tuple[xr.Dataset, str, ndarray, ndarray],
):
    ds_res, ds_qu, coupler = setup_q12_q13_data
    a = ResonatorSpectroscopyVsCurrentCouplerAnalysis(
        "resonator_spectroscopy_vs_current", ["resonator_crossing_points"]
    )
    qoi = a.process_coupler(ds_res, coupler)
    update_redis_trusted_values(
        "resonator_spectroscopy_vs_current", coupler, qoi, ["resonator_crossing_points"]
    )

    b = QubitSpectroscopyVsCurrentCouplerAnalysis("name", ["crossing_points"])
    qoi = b.process_coupler(ds_qu, coupler)

    q12_crossings = getCrossingForQubit(qoi, "q14")
    q13_crossings = getCrossingForQubit(qoi, "q15")
    assert q12_crossings == pytest.approx(
        [-0.00195, -0.00105, 0.001475, 0.002375], abs=1e-6
    )
    assert q13_crossings == pytest.approx(
        [-0.002125, 0.001375],
        abs=1e-6,
    )


@pytest.fixture(autouse=False)
def setup_q14_q15_data():
    coupler = "q14_q15"
    ds_qu, ds_res = get_dataset_for_coupler(coupler)
    return ds_res, ds_qu, coupler


def test_get_crossings_for_q14_q15(
    setup_q14_q15_data: tuple[xr.Dataset, str, ndarray, ndarray],
):
    ds_res, ds_qu, coupler = setup_q14_q15_data
    a = ResonatorSpectroscopyVsCurrentCouplerAnalysis(
        "resonator_spectroscopy_vs_current", ["resonator_crossing_points"]
    )
    qoi = a.process_coupler(ds_res, coupler)
    update_redis_trusted_values(
        "resonator_spectroscopy_vs_current", coupler, qoi, ["resonator_crossing_points"]
    )

    b = QubitSpectroscopyVsCurrentCouplerAnalysis("name", ["crossing_points"])
    qoi = b.process_coupler(ds_qu, coupler)

    q14_crossings = getCrossingForQubit(qoi, "q14")
    q15_crossings = getCrossingForQubit(qoi, "q15")
    assert q14_crossings == pytest.approx([-0.0018, -0.00095, 0.00165], abs=1e-6)
    assert q15_crossings == pytest.approx([-0.00185, -0.000825, 0.00155], abs=1e-6)


@with_os_env({"DATA_DIR": str(Path(__file__).parent / "results")})
def test_coupler_plot_is_created(setup_q06_q07_data):
    matplotlib.use("Agg")
    ds, coupler = setup_q06_q07_data
    a = QubitSpectroscopyVsCurrentCouplerAnalysis("name", ["crossing_points"])
    a.process_coupler(ds, coupler)

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
    a = QubitSpectroscopyVsCurrentCouplerAnalysis("name", ["crossing_points"])
    a.process_coupler(ds, coupler)

    path = Path(os.environ["DATA_DIR"])
    a.plot_spectroscopies(path)

    figure_1_path = (
        os.environ["DATA_DIR"] + "/coupler_spectroscopy_q06_q07_q06_spectroscopies.png"
    )
    assert os.path.exists(figure_1_path)
    from PIL import Image

    with Image.open(figure_1_path) as img:
        assert img.format == "PNG", "File should be a PNG image"

    figure_2_path = (
        os.environ["DATA_DIR"] + "/coupler_spectroscopy_q06_q07_q07_spectroscopies.png"
    )
    assert os.path.exists(figure_2_path)
    from PIL import Image

    with Image.open(figure_2_path) as img:
        assert img.format == "PNG", "File should be a PNG image"
