import os
from pathlib import Path
import matplotlib
from matplotlib import pyplot as plt
import numpy as np
import numpy.testing as npt
import pytest
import xarray as xr
from tergite_autocalibration.lib.base.analysis import BaseAnalysis
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis import (
    CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis import (
    CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis,
)


@pytest.fixture(autouse=True)
def setup_good_data():
    os.environ["DATA_DIR"] = str(Path(__file__).parent / "results")
    dataset_path = Path(__file__).parent / "data" / "dataset_good_quality_freq_amp.hdf5"
    print(dataset_path)
    ds = xr.open_dataset(dataset_path)
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d14 = ds.yq14.to_dataset()
    d15 = ds.yq15.to_dataset()
    d14.yq14.attrs["qubit"] = "q14"
    d15.yq15.attrs["qubit"] = "q15"
    freqs = ds[f"cz_pulse_frequenciesq14_q15"].values  # MHz
    amps = ds[f"cz_pulse_amplitudesq14_q15"].values  # uA
    return d14, d15, freqs, amps


def test_canCreateCorrectClass(setup_good_data):
    d14, d15, freqs, amps = setup_good_data
    c = CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis(d14, freqs, amps)
    assert isinstance(c, CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis)
    assert isinstance(c, BaseAnalysis)
    c = CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis(d15, freqs, amps)
    assert isinstance(c, CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis)
    assert isinstance(c, BaseAnalysis)


def test_hasCorrectFreqsAndAmps(setup_good_data):
    d14, d15, freqs, amps = setup_good_data
    c14 = CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis(d14, freqs, amps)
    npt.assert_array_equal(c14.frequencies, freqs)
    npt.assert_array_equal(c14.amplitudes, amps)
    c15 = CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis(d15, freqs, amps)
    npt.assert_array_equal(c15.frequencies, freqs)
    npt.assert_array_equal(c15.amplitudes, amps)


def test_dataIsReadCorrectly(setup_good_data):
    d14, d15, freqs, amps = setup_good_data
    c14 = CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis(d14, freqs, amps)
    npt.assert_array_equal(c14.dataset[f"y{c14.qubit}"].values, d14[f"yq14"].values)
    c15 = CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis(d15, freqs, amps)
    npt.assert_array_equal(c15.dataset[f"y{c15.qubit}"].values, d15[f"yq15"].values)


def test_datasetHasQubitDefined(setup_good_data):
    d14, d15, freqs, amps = setup_good_data
    c = CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis(d14, freqs, amps)
    assert c.qubit == "q14"
    c = CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis(d15, freqs, amps)
    assert c.qubit == "q15"


def test_canGetMaxFromQ1(setup_good_data):
    d14, d15, freqs, amps = setup_good_data
    c = CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis(d14, freqs, amps)
    result = c.run_fitting()
    indexBestFreq = np.where(freqs == result[0])[0]
    indexBestAmp = np.where(amps == result[1])[0]
    assert indexBestFreq[0] == 9
    assert indexBestAmp[0] == 13


def test_canGetMinFromQ2(setup_good_data):
    d14, d15, freqs, amps = setup_good_data
    c = CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis(d15, freqs, amps)
    result = c.run_fitting()
    indexBestFreq = np.where(freqs == result[0])[0]
    indexBestAmp = np.where(amps == result[1])[0]
    assert indexBestFreq[0] == 10
    assert indexBestAmp[0] == 12


def test_canPlot(setup_good_data):
    matplotlib.use("Agg")
    d14, d15, freqs, amps = setup_good_data
    c14 = CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis(d14, freqs, amps)
    result = c14.run_fitting()

    figure_path = os.environ["DATA_DIR"] + "/Frequency_Amplitude_q14.png"
    # Remove the file if it already exists
    if os.path.exists(figure_path):
        os.remove(figure_path)

    fig, ax = plt.subplots(figsize=(15, 7), num=1)
    plt.Axes
    c14.plotter(ax)
    fig.savefig(figure_path)
    plt.close()

    assert os.path.exists(figure_path)
    from PIL import Image

    with Image.open(figure_path) as img:
        assert img.format == "PNG", "File should be a PNG image"

    c15 = CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis(d15, freqs, amps)
    result = c15.run_fitting()

    figure_path = os.environ["DATA_DIR"] + "/Frequency_Amplitude_q15.png"
    # Remove the file if it already exists
    if os.path.exists(figure_path):
        os.remove(figure_path)

    fig, ax = plt.subplots(figsize=(15, 7), num=1)
    plt.Axes
    c15.plotter(ax)
    fig.savefig(figure_path)
    plt.close()

    assert os.path.exists(figure_path)
    from PIL import Image

    with Image.open(figure_path) as img:
        assert img.format == "PNG", "File should be a PNG image"


@pytest.fixture(autouse=True)
def setup_bad_data():
    os.environ["DATA_DIR"] = str(Path(__file__).parent / "results")
    dataset_path = Path(__file__).parent / "data" / "dataset_bad_quality_freq_amp.hdf5"
    print(dataset_path)
    ds = xr.open_dataset(dataset_path)
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d14 = ds.yq14.to_dataset()
    d15 = ds.yq15.to_dataset()
    d14.yq14.attrs["qubit"] = "q14"
    d15.yq15.attrs["qubit"] = "q15"
    freqs = ds[f"cz_pulse_frequenciesq14_q15"].values  # MHz
    amps = ds[f"cz_pulse_amplitudesq14_q15"].values  # uA
    return d14, d15, freqs, amps


def test_canPlotBad(setup_bad_data):
    matplotlib.use("Agg")
    d14, d15, freqs, amps = setup_bad_data
    c14 = CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis(d14, freqs, amps)
    result = c14.run_fitting()

    figure_path = os.environ["DATA_DIR"] + "/Frequency_Amplitude_bad_q14.png"
    # Remove the file if it already exists
    if os.path.exists(figure_path):
        os.remove(figure_path)

    fig, ax = plt.subplots(figsize=(15, 7), num=1)
    plt.Axes
    c14.plotter(ax)
    fig.savefig(figure_path)
    plt.close()

    assert os.path.exists(figure_path)
    from PIL import Image

    with Image.open(figure_path) as img:
        assert img.format == "PNG", "File should be a PNG image"

    c15 = CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis(d15, freqs, amps)
    result = c15.run_fitting()

    figure_path = os.environ["DATA_DIR"] + "/Frequency_Amplitude_bad_q15.png"
    # Remove the file if it already exists
    if os.path.exists(figure_path):
        os.remove(figure_path)

    fig, ax = plt.subplots(figsize=(15, 7), num=1)
    plt.Axes
    c15.plotter(ax)
    fig.savefig(figure_path)
    plt.close()

    assert os.path.exists(figure_path)
    from PIL import Image

    with Image.open(figure_path) as img:
        assert img.format == "PNG", "File should be a PNG image"
