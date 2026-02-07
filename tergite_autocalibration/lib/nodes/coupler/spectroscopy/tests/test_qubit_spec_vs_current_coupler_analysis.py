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
import re
from pathlib import Path

import matplotlib
import pytest
import xarray as xr
from matplotlib import pyplot as plt
from numpy import ndarray

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.analysis import BaseAnalysis, BaseCouplerAnalysis
from tergite_autocalibration.lib.nodes.coupler.spectroscopy.analysis import (
    CouplerAnticrossingAnalysis,
    ResonatorSpectroscopyVsCurrentCouplerAnalysis,
)
from tergite_autocalibration.lib.utils.redis import update_redis_trusted_values
from tergite_autocalibration.tests.utils.decorators import with_os_env
from tergite_autocalibration.utils.dto.qoi import QOI


def test_CanCreate():
    a = CouplerAnticrossingAnalysis("name", ["redis_field"])
    assert isinstance(a, CouplerAnticrossingAnalysis)
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
    return ds_qu, ds_res


def getCrossingForQubit(qoi: QOI, qubit: str = "q06"):
    results = qoi.analysis_result
    qubit_number = int(re.sub("[^0-9]", "", qubit))
    if qubit_number % 2 == 0:
        crossing_points = "control_qubit_crossing_points"
    elif qubit_number % 2 == 1:
        crossing_points = "target_qubit_crossing_points"
    else:
        raise ValueError("Invalid qubit number")
    crossings = results[crossing_points]["value"]
    return crossings


res_coupler_qois = [
    "control_resonator_crossing_points",
    "target_resonator_crossing_points",
]
qubit_coupler_qois = ["control_qubit_crossing_points", "target_qubit_crossing_points"]


def test_get_crossings_for_q06_q07(
    setup_q06_q07_data: tuple[xr.Dataset, str, ndarray, str],
):
    ds_res, ds_qu, coupler = setup_q06_q07_data
    a = ResonatorSpectroscopyVsCurrentCouplerAnalysis(
        "resonator_spectroscopy_vs_current", res_coupler_qois
    )
    q1, q2 = coupler.split("_")
    REDIS_CONNECTION.hset(f"couplers:{coupler}", "control_qubit", q1)
    REDIS_CONNECTION.hset(f"couplers:{coupler}", "target_qubit", q2)
    qoi = a.process_coupler(ds_res, coupler)
    update_redis_trusted_values(
        "resonator_spectroscopy_vs_current", coupler, qoi, res_coupler_qois
    )

    b = CouplerAnticrossingAnalysis("name", qubit_coupler_qois)
    qoi = b.process_coupler(ds_qu, coupler)

    q06_crossings = getCrossingForQubit(qoi, "q06")
    q07_crossings = getCrossingForQubit(qoi, "q07")

    assert q06_crossings == pytest.approx(
        [-0.001925, -0.0011, 0.001375, 0.0022], abs=1e-6
    )
    assert q07_crossings == pytest.approx(
        [-0.002025, -0.001, 0.0012875, 0.0023],
        abs=1e-6,
    )


@pytest.fixture(autouse=False)
def setup_q08_q09_data():
    coupler = "q08_q09"
    ds_qu, ds_res = get_dataset_for_coupler(coupler)
    return ds_res, ds_qu, coupler


def test_get_crossings_for_q08_q09(
    setup_q08_q09_data: tuple[xr.Dataset, str, ndarray, str],
):
    ds_res, ds_qu, coupler = setup_q08_q09_data
    a = ResonatorSpectroscopyVsCurrentCouplerAnalysis(
        "resonator_spectroscopy_vs_current", res_coupler_qois
    )
    q1, q2 = coupler.split("_")
    REDIS_CONNECTION.hset(f"couplers:{coupler}", "control_qubit", q1)
    REDIS_CONNECTION.hset(f"couplers:{coupler}", "target_qubit", q2)
    qoi = a.process_coupler(ds_res, coupler)
    update_redis_trusted_values(
        "resonator_spectroscopy_vs_current", coupler, qoi, res_coupler_qois
    )

    b = CouplerAnticrossingAnalysis("name", qubit_coupler_qois)
    qoi = b.process_coupler(ds_qu, coupler)

    q08_crossings = getCrossingForQubit(qoi, "q08")
    q09_crossings = getCrossingForQubit(qoi, "q09")
    assert q08_crossings == pytest.approx(
        [-0.00215, -0.00135, 0.001325, 0.002125],
        abs=1e-6,
    )
    assert q09_crossings == pytest.approx(
        [-0.0023625, -0.0011375, 0.0011, 0.0022875],
        abs=1e-6,
    )


@pytest.fixture(autouse=False)
def setup_q12_q13_data():
    coupler = "q12_q13"
    ds_qu, ds_res = get_dataset_for_coupler(coupler)
    return ds_res, ds_qu, coupler


def test_get_crossings_for_q12_q13(
    setup_q12_q13_data: tuple[xr.Dataset, xr.Dataset, str],
):
    ds_res, ds_qu, coupler = setup_q12_q13_data
    a = ResonatorSpectroscopyVsCurrentCouplerAnalysis(
        "resonator_spectroscopy_vs_current", res_coupler_qois
    )
    q1, q2 = coupler.split("_")
    REDIS_CONNECTION.hset(f"couplers:{coupler}", "control_qubit", q1)
    REDIS_CONNECTION.hset(f"couplers:{coupler}", "target_qubit", q2)
    qoi = a.process_coupler(ds_res, coupler)
    update_redis_trusted_values(
        "resonator_spectroscopy_vs_current", coupler, qoi, res_coupler_qois
    )

    b = CouplerAnticrossingAnalysis("name", qubit_coupler_qois)
    qoi = b.process_coupler(ds_qu, coupler)

    q12_crossings = getCrossingForQubit(qoi, "q12")
    q13_crossings = getCrossingForQubit(qoi, "q13")
    assert q12_crossings == pytest.approx(
        [-0.00190, -0.00105, 0.001475, 0.002375], abs=1e-6
    )
    assert q13_crossings == pytest.approx(
        [-0.0020875, 0.001375],
        abs=1e-6,
    )


@pytest.fixture(autouse=False)
def setup_q14_q15_data():
    coupler = "q14_q15"
    ds_qu, ds_res = get_dataset_for_coupler(coupler)
    return ds_res, ds_qu, coupler


def test_get_crossings_for_q14_q15(
    setup_q14_q15_data: tuple[xr.Dataset, xr.Dataset, str],
):
    ds_res, ds_qu, coupler = setup_q14_q15_data
    a = ResonatorSpectroscopyVsCurrentCouplerAnalysis(
        "resonator_spectroscopy_vs_current", res_coupler_qois
    )
    q1, q2 = coupler.split("_")
    REDIS_CONNECTION.hset(f"couplers:{coupler}", "control_qubit", q1)
    REDIS_CONNECTION.hset(f"couplers:{coupler}", "target_qubit", q2)
    qoi = a.process_coupler(ds_res, coupler)
    update_redis_trusted_values(
        "resonator_spectroscopy_vs_current", coupler, qoi, res_coupler_qois
    )

    b = CouplerAnticrossingAnalysis("name", qubit_coupler_qois)
    qoi = b.process_coupler(ds_qu, coupler)

    q14_crossings = getCrossingForQubit(qoi, "q14")
    q15_crossings = getCrossingForQubit(qoi, "q15")
    assert q14_crossings == pytest.approx([-0.0018, -0.00095, 0.00165], abs=1e-6)
    assert q15_crossings == pytest.approx([-0.00185, -0.000825, 0.00155], abs=1e-6)


@with_os_env({"DATA_DIR": str(Path(__file__).parent / "results")})
def test_coupler_plot_is_created(setup_q06_q07_data):
    matplotlib.use("Agg")
    ds_res, ds_qu, coupler = setup_q06_q07_data
    a = ResonatorSpectroscopyVsCurrentCouplerAnalysis(
        "resonator_spectroscopy_vs_current", res_coupler_qois
    )
    qoi = a.process_coupler(ds_res, coupler)
    update_redis_trusted_values(
        "resonator_spectroscopy_vs_current", coupler, qoi, res_coupler_qois
    )

    b = CouplerAnticrossingAnalysis("qubit_spectroscopy_vs_current", qubit_coupler_qois)
    qoi = b.process_coupler(ds_qu, coupler)

    figure_path = os.environ["DATA_DIR"] + "/qubit_spectroscopy_vs_current.png"
    # Remove the file if it already exists
    if os.path.exists(figure_path):
        os.remove(figure_path)

    figures_dictionary = {}
    b.plotter(figures_dictionary)
    fig_list = figures_dictionary[coupler]
    fig = fig_list[0]
    fig.savefig(figure_path)
    plt.close()

    assert os.path.exists(figure_path)
    from PIL import Image

    with Image.open(figure_path) as img:
        assert img.format == "PNG", "File should be a PNG image"


@pytest.fixture(autouse=False)
def setup_q16_q17_data():
    dataset_path = (
        Path(__file__).parent
        / "data"
        / "dataset_qubit_spectroscopy_vs_current_no_crossings.hdf5"
    )
    ds = xr.open_dataset(dataset_path)
    coupler = "q16_q17"
    ds = xr.merge(ds[var] for var in ["yq16", "yq17"])
    ds.attrs["coupler"] = coupler
    return ds, coupler


@pytest.mark.skip()
def test_no_crossings_for_q16_q17(
    setup_q16_q17_data: tuple[xr.Dataset, str, ndarray, ndarray],
):
    ds, coupler = setup_q16_q17_data
    a = CouplerAnticrossingAnalysis("name", qubit_coupler_qois)
    qoi = a.process_coupler(ds, coupler)

    q16_crossings = getCrossingForQubit(qoi, "q16")
    q17_crossings = getCrossingForQubit(qoi, "q17")
    assert q16_crossings == pytest.approx([0.000975], abs=1e-6)
    assert len(q17_crossings) == 0


@pytest.mark.skip()
@with_os_env({"DATA_DIR": str(Path(__file__).parent / "results")})
def test_qubit_spectroscopies_for_coupler_are_created(setup_q06_q07_data):
    matplotlib.use("Agg")
    ds_res, ds_qu, coupler = setup_q06_q07_data
    a = ResonatorSpectroscopyVsCurrentCouplerAnalysis(
        "resonator_spectroscopy_vs_current", res_coupler_qois
    )
    qoi = a.process_coupler(ds_res, coupler)
    update_redis_trusted_values(
        "resonator_spectroscopy_vs_current", coupler, qoi, res_coupler_qois
    )

    b = CouplerAnticrossingAnalysis("qs_vs_current", qubit_coupler_qois)
    qoi = b.process_coupler(ds_qu, coupler)

    path = Path(os.environ["DATA_DIR"])
    b.plot_spectroscopies(path)

    figure_1_path = (
        os.environ["DATA_DIR"] + "/qs_vs_current_q06_q07_q06_spectroscopies.png"
    )
    assert os.path.exists(figure_1_path)
    from PIL import Image

    with Image.open(figure_1_path) as img:
        assert img.format == "PNG", "File should be a PNG image"

    figure_2_path = (
        os.environ["DATA_DIR"] + "/qs_vs_current_q06_q07_q07_spectroscopies.png"
    )
    assert os.path.exists(figure_2_path)

    with Image.open(figure_2_path) as img:
        assert img.format == "PNG", "File should be a PNG image"


@pytest.mark.skip()
@with_os_env({"DATA_DIR": str(Path(__file__).parent / "results")})
def test_qubit_spectroscopies_for_coupler_are_created_when_no_crossings(
    setup_q16_q17_data,
):
    matplotlib.use("Agg")
    ds, coupler = setup_q16_q17_data
    a = CouplerAnticrossingAnalysis("qs_vs_current", qubit_coupler_qois)
    qoi = a.process_coupler(ds, coupler)

    path = Path(os.environ["DATA_DIR"])
    a.plot_spectroscopies(path)

    figure_1_path = (
        os.environ["DATA_DIR"] + "/qs_vs_current_q16_q17_q16_spectroscopies.png"
    )
    assert os.path.exists(figure_1_path)
    from PIL import Image

    with Image.open(figure_1_path) as img:
        assert img.format == "PNG", "File should be a PNG image"

    figure_2_path = (
        os.environ["DATA_DIR"] + "/qs_vs_current_q16_q17_q17_spectroscopies.png"
    )
    assert os.path.exists(figure_2_path)

    with Image.open(figure_2_path) as img:
        assert img.format == "PNG", "File should be a PNG image"
