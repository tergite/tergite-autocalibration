from pathlib import Path
import numpy as np
import pytest
import xarray as xr

from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.analysis import (
    CombinedFrequencyVsAmplitudeAnalysis,
    FrequencyVsAmplitudeQ1Analysis,
    FrequencyVsAmplitudeQ2Analysis,
)


@pytest.fixture(autouse=True)
def setup_good_data():
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
    q14Ana = FrequencyVsAmplitudeQ1Analysis(d14, freqs, amps)
    q14Res = q14Ana.run_fitting()
    q15Ana = FrequencyVsAmplitudeQ2Analysis(d15, freqs, amps)
    q15Res = q15Ana.run_fitting()
    return q14Res, q15Res, freqs, amps


def test_combineResultsReturnCorrectClass(setup_good_data):
    q14Res, q15Res, freqs, amps = setup_good_data
    c = CombinedFrequencyVsAmplitudeAnalysis(q14Res, q15Res)
    assert isinstance(c, CombinedFrequencyVsAmplitudeAnalysis)


def test_combineGoodResultsReturnOneValidPoint(setup_good_data):
    q14Res, q15Res, freqs, amps = setup_good_data
    c = CombinedFrequencyVsAmplitudeAnalysis(q14Res, q15Res)
    r = c.are_frequencies_compatible()
    assert r
    r = c.are_amplitudes_compatible()
    assert r
    r = c.are_two_qubits_compatible()
    assert r


def test_combineGoodResultsReturnCorrectResults(setup_good_data):
    q14Res, q15Res, freqs, amps = setup_good_data
    c = CombinedFrequencyVsAmplitudeAnalysis(q14Res, q15Res)
    r = c.best_parameters()
    assert r[0] == (freqs[10] + freqs[9]) / 2
    assert r[1] == (amps[12] + amps[13]) / 2


@pytest.fixture(autouse=True)
def setup_bad_data():
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
    q14Ana = FrequencyVsAmplitudeQ1Analysis(d14, freqs, amps)
    q14Res = q14Ana.run_fitting()
    q15Ana = FrequencyVsAmplitudeQ2Analysis(d15, freqs, amps)
    q15Res = q15Ana.run_fitting()
    return q14Res, q15Res


def test_combineBadResultsReturnNoValidPoint(setup_bad_data):
    q14Res, q15Res = setup_bad_data
    c = CombinedFrequencyVsAmplitudeAnalysis(q14Res, q15Res)
    r = c.are_frequencies_compatible()
    assert r == False
    r = c.are_amplitudes_compatible()
    assert r == False
    r = c.are_two_qubits_compatible()
    assert r == False
