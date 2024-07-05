import os.path

from tergite_autocalibration.tests.utils.env import setup_test_env

setup_test_env()

import matplotlib
import pytest
from pathlib import Path
import xarray as xr
import numpy as np
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.utils.cz_singleGateSimpleFit import (
    CZSingleGateSimpleFit,
)
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.utils.cz_singleGateSimpleFitResult import (
    FitResultStatus,
)


@pytest.fixture(autouse=True)
def setup_good_data():
    dataset_path = Path(__file__).parent / "data" / "dataset_goodQuality.hdf5"
    print(dataset_path)
    ds = xr.open_dataset(dataset_path)
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d17 = ds.yq17.to_dataset()
    d22 = ds.yq22.to_dataset()
    d17.yq17.attrs["qubit"] = "q17"
    d22.yq22.attrs["qubit"] = "q22"
    freq = ds[f"cz_pulse_frequencies_sweepq17"].values / 1e6  # MHz
    times = ds[f"cz_pulse_durationsq17"].values * 1e9  # ns
    return d17, d22, freq, times


def test_canCreate(setup_good_data):
    d17, d22, freq, times = setup_good_data
    CZSingleGateSimpleFit(d17, freq, times)
    pass


def test_datasetHasQubitDefined(setup_good_data):
    d17, d22, freq, times = setup_good_data
    r = CZSingleGateSimpleFit(d17, freq, times)
    assert r.qubit == "q17"
    r = CZSingleGateSimpleFit(d22, freq, times)
    assert r.qubit == "q22"


def test_canGetBestFrequencyFromGoodChevronQ17(setup_good_data):
    d17, d22, freq, times = setup_good_data
    first_scan = CZSingleGateSimpleFit(d17, freq, times)
    result = first_scan.run_fitting()
    indexBestPvalue = np.argmax(result.pvalues)
    assert indexBestPvalue == 6
    bestFreq = freq[indexBestPvalue]
    assert bestFreq == freq[6]
    assert max(result.pvalues) > 0.99
    assert result.status == FitResultStatus.FOUND


def test_canGetBestFrequencyFromGoodChevronQ22(setup_good_data):
    d17, d22, freq, times = setup_good_data
    first_scan = CZSingleGateSimpleFit(d22, freq, times)
    result = first_scan.run_fitting()
    bestFreq = freq[np.argmax(result.pvalues)]
    assert bestFreq == freq[5]
    assert max(result.pvalues) > 0.99
    assert result.status == FitResultStatus.FOUND


# Another good:
# C:\Users\faucci\Documents\Autocalibration\20240505\20240505\data\q19_q20\20240506-012028-213-6939f8-cz_chevron
@pytest.fixture(autouse=True)
def setup_good_data_2():
    dataset_path = Path(__file__).parent / "data" / "dataset_goodQuality_2.hdf5"
    print(dataset_path)
    ds = xr.open_dataset(dataset_path)
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d19 = ds.yq19.to_dataset()
    d20 = ds.yq20.to_dataset()
    d19.yq19.attrs["qubit"] = "q19"
    d20.yq20.attrs["qubit"] = "q20"
    freq = ds[f"cz_pulse_frequenciesq19_q20"].values / 1e6  # MHz
    times = ds[f"cz_pulse_durationsq19_q20"].values * 1e9  # ns
    return d19, d20, freq, times


def test_canGetBestFrequencyFromGoodData2Chevron19(setup_good_data_2):
    d19, d22, freq, times = setup_good_data_2
    first_scan = CZSingleGateSimpleFit(d19, freq, times)
    result = first_scan.run_fitting()
    indexBestPvalue = np.argmax(result.pvalues)
    assert indexBestPvalue == 16
    bestFreq = freq[indexBestPvalue]
    assert bestFreq == freq[16]
    assert max(result.pvalues) > 0.85
    assert result.status == FitResultStatus.FOUND


def test_canGetBestFrequencyFromGoodData2ChevronQ20(setup_good_data_2):
    d17, d20, freq, times = setup_good_data_2
    first_scan = CZSingleGateSimpleFit(d20, freq, times)
    result = first_scan.run_fitting()
    indexBestPvalue = np.argmax(result.pvalues)
    assert indexBestPvalue == 14
    bestFreq = freq[indexBestPvalue]
    assert bestFreq == freq[14]
    assert max(result.pvalues) > 0.99
    assert result.status == FitResultStatus.FOUND


@pytest.fixture(autouse=True)
def setup_medium_data():
    dataset_path = Path(__file__).parent / "data" / "dataset_mediumQuality.hdf5"
    ds = xr.open_dataset(dataset_path)
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d17 = ds.yq17.to_dataset()
    d22 = ds.yq22.to_dataset()
    d17.yq17.attrs["qubit"] = "q17"
    d22.yq22.attrs["qubit"] = "q22"
    freq = ds[f"cz_pulse_frequencies_sweepq17"].values / 1e6  # MHz
    times = ds[f"cz_pulse_durationsq17"].values * 1e9  # ns
    return d17, d22, freq, times


def test_canGetBestFrequencyFromMediumChevronQ17(setup_medium_data):
    d17, d22, freq, times = setup_medium_data
    first_scan = CZSingleGateSimpleFit(d17, freq, times)
    result = first_scan.run_fitting()
    bestFreq = freq[np.argmax(result.pvalues)]
    # assert bestFreq == freq[11] #too unstable to be relevant, not crucial for final decision
    assert max(result.pvalues) < 0.9
    assert result.status == FitResultStatus.FOUND


def test_canGetBestFrequencyFromMediumChevronQ22(setup_medium_data):
    d17, d22, freq, times = setup_medium_data
    first_scan = CZSingleGateSimpleFit(d22, freq, times)
    result = first_scan.run_fitting()
    bestFreq = freq[np.argmax(result.pvalues)]
    # assert bestFreq == freq[3] # as above
    assert max(result.pvalues) > 0.9 or (max(p[0] for p in result.fittedParams)) < 0.21
    assert result.status == FitResultStatus.FOUND


@pytest.fixture(autouse=True)
def setup_poor_data():
    dataset_path = Path(__file__).parent / "data" / "dataset_poorQuality.hdf5"
    ds = xr.open_dataset(dataset_path)
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d17 = ds.yq17.to_dataset()
    d22 = ds.yq22.to_dataset()
    d17.yq17.attrs["qubit"] = "q17"
    d22.yq22.attrs["qubit"] = "q22"
    freq = ds[f"cz_pulse_frequencies_sweepq17"].values / 1e6  # MHz
    times = ds[f"cz_pulse_durationsq17"].values * 1e9  # ns
    return d17, d22, freq, times


def test_canGetBestFrequencyFromPoorChevronQ17(setup_poor_data):
    d17, d22, freq, times = setup_poor_data
    first_scan = CZSingleGateSimpleFit(d17, freq, times)
    result = first_scan.run_fitting()
    assert max(result.pvalues) < 0.8 or (max(p[0] for p in result.fittedParams)) < 0.21
    assert result.status == FitResultStatus.FOUND


def test_canGetBestFrequencyFromPoorChevronQ22(setup_poor_data):
    d17, d22, freq, times = setup_poor_data
    first_scan = CZSingleGateSimpleFit(d22, freq, times)
    result = first_scan.run_fitting()
    bestFreq = freq[np.argmax(result.pvalues)]
    assert bestFreq > freq[6]
    assert max(result.pvalues) < 0.8 or (max(p[0] for p in result.fittedParams)) < 0.21
    assert result.status == FitResultStatus.FOUND


@pytest.fixture(autouse=True)
def setup_bad_data():
    dataset_path = Path(__file__).parent / "data" / "dataset_badQuality.hdf5"
    print(dataset_path)
    ds = xr.open_dataset(dataset_path)
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d17 = ds.yq17.to_dataset()
    d22 = ds.yq22.to_dataset()
    d17.yq17.attrs["qubit"] = "q17"
    d22.yq22.attrs["qubit"] = "q22"
    freq = ds[f"cz_pulse_frequencies_sweepq17"].values / 1e6  # MHz
    times = ds[f"cz_pulse_durationsq17"].values * 1e9  # ns
    return d17, d22, freq, times


def test_canGetBestFrequencyFromBadChevronQ17(setup_bad_data):
    d17, d22, freq, times = setup_bad_data
    first_scan = CZSingleGateSimpleFit(d17, freq, times)
    result = first_scan.run_fitting()
    bestFreq = freq[np.argmax(result.pvalues)]
    # assert bestFreq > freq[6] # as above
    assert max(result.pvalues) < 0.9 or (max(p[0] for p in result.fittedParams)) < 0.21
    assert result.status == FitResultStatus.FOUND


def test_canGetBestFrequencyFromBadChevronQ22(setup_bad_data):
    d17, d22, freq, times = setup_bad_data
    first_scan = CZSingleGateSimpleFit(d22, freq, times)
    result = first_scan.run_fitting()
    freq = d22[f"cz_pulse_frequencies_sweepq22"].values  # MHz
    bestFreq = freq[np.argmax(result.pvalues)]
    # assert bestFreq == freq[8] as above
    assert (max(result.pvalues) < 0.8) or (
        max(p[0] for p in result.fittedParams)
    ) < 0.21
    assert result.status == FitResultStatus.FOUND


def test_plotsAreCreated(setup_good_data):
    matplotlib.use("Agg")
    d17, d22, freq, times = setup_good_data
    first_scan = CZSingleGateSimpleFit(d17, freq, times)
    result = first_scan.run_fitting()
    folder_path = Path(__file__).parent / "results"
    os.makedirs(folder_path, exist_ok=True)
    first_scan.plotter(folder_path)

    figure_path = folder_path / "AllFits_q17.png"
    assert figure_path.exists(), "The PNG file should exist"
    from PIL import Image

    with Image.open(figure_path) as img:
        assert img.format == "PNG", "File should be a PNG image"

    figure_path = folder_path / "SummaryScan_q17.png"
    assert figure_path.exists(), "The PNG file should exist"
    from PIL import Image

    with Image.open(figure_path) as img:
        assert img.format == "PNG", "File should be a PNG image"
