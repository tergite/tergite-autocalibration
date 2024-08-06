from pathlib import Path
from numpy import ndarray
import xarray as xr
import pytest

from tergite_autocalibration.lib.base.analysis import BaseAnalysis

from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.analysis import (
    CZParametrisationFixDurationAnalysis,
    CombinedFrequencyVsAmplitudeAnalysis,
    FrequencyVsAmplitudeQ1Analysis,
    FrequencyVsAmplitudeQ2Analysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.utils.NoValidCombinationException import (
    NoValidCombinationException,
)


def test_CanCreate():
    a = CZParametrisationFixDurationAnalysis()
    assert isinstance(a, CZParametrisationFixDurationAnalysis)
    assert isinstance(a, BaseAnalysis)


@pytest.fixture(autouse=True)
def setup_data():
    # It should be a single dataset, but we do not have one yet, so we loop over existing files
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
    c1 = CombinedFrequencyVsAmplitudeAnalysis(q14Res, q15Res)

    dataset_path = Path(__file__).parent / "data" / "dataset_bad_quality_freq_amp.hdf5"
    ds = xr.open_dataset(dataset_path)
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d14 = ds.yq14.to_dataset()
    d15 = ds.yq15.to_dataset()
    d14.yq14.attrs["qubit"] = "q14"
    d15.yq15.attrs["qubit"] = "q15"
    freqs_bad = ds[f"cz_pulse_frequenciesq14_q15"].values  # MHz
    amps_bad = ds[f"cz_pulse_amplitudesq14_q15"].values  # uA
    q14Ana = FrequencyVsAmplitudeQ1Analysis(
        d14, freqs_bad, amps_bad
    )
    q14Res = q14Ana.run_fitting()
    q15Ana = FrequencyVsAmplitudeQ2Analysis(
        d15, freqs_bad, amps_bad
    )
    q15Res = q15Ana.run_fitting()
    c2 = CombinedFrequencyVsAmplitudeAnalysis(q14Res, q15Res)

    dataset_path = (
        Path(__file__).parent / "data" / "dataset_good_quality_freq_amp_2.hdf5"
    )
    ds = xr.open_dataset(dataset_path)
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d14 = ds.yq14.to_dataset()
    d15 = ds.yq15.to_dataset()
    d14.yq14.attrs["qubit"] = "q14"
    d15.yq15.attrs["qubit"] = "q15"
    freqs_2 = ds[f"cz_pulse_frequenciesq14_q15"].values  # MHz
    amps_2 = ds[f"cz_pulse_amplitudesq14_q15"].values  # uA
    q14Ana = FrequencyVsAmplitudeQ1Analysis(d14, freqs_2, amps_2)
    q14Res = q14Ana.run_fitting()
    q15Ana = FrequencyVsAmplitudeQ2Analysis(d15, freqs_2, amps_2)
    q15Res = q15Ana.run_fitting()
    c3 = CombinedFrequencyVsAmplitudeAnalysis(q14Res, q15Res)

    list_of_results = [(c1, 0.1), (c2, 0.2), (c3, 0.3)]
    return list_of_results, freqs, amps, freqs_2, amps_2


def test_PickLowestCurrent(setup_data: tuple[list[tuple[CombinedFrequencyVsAmplitudeAnalysis, float]], ndarray, ndarray, ndarray, ndarray]):
    list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    a = CZParametrisationFixDurationAnalysis()
    a.run_analysis_on_freq_amp_results(list_of_results)

    assert a.opt_index == 0
    assert a.opt_freq == (freqs[10] + freqs[9]) / 2
    assert a.opt_amp == (amps[12] + amps[13]) / 2
    assert a.opt_current == 0.1


def test_PickLowestCurrentWithoutBest(setup_data: tuple[list[tuple[CombinedFrequencyVsAmplitudeAnalysis, float]], ndarray, ndarray, ndarray, ndarray]):
    list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    list_of_results.pop(0)
    a = CZParametrisationFixDurationAnalysis()
    a.run_analysis_on_freq_amp_results(list_of_results)

    assert (
        a.opt_index == 1
    )  # I removed the first, so the good point is now the last which is in position 1
    assert a.opt_freq == freqs_2[5]
    assert a.opt_amp == amps_2[10]
    assert a.opt_current == 0.3


def test_ReturnErrorIfNoGoodPoint(setup_data: tuple[list[tuple[CombinedFrequencyVsAmplitudeAnalysis, float]], ndarray, ndarray, ndarray, ndarray]):
    list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    print(len(list_of_results))
    list_of_results.pop(2)
    list_of_results.pop(0)
    a = CZParametrisationFixDurationAnalysis()
    print(issubclass(NoValidCombinationException, Exception))

    with pytest.raises(NoValidCombinationException, match="No valid combination found"):
        a.run_analysis_on_freq_amp_results(list_of_results)

def test_PickGoodValueIfSmallestInAbsolute(setup_data: tuple[list[tuple[CombinedFrequencyVsAmplitudeAnalysis, float]], ndarray, ndarray, ndarray, ndarray]):
    list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    print(len(list_of_results))
    new_element = (list_of_results[2][0], -0.3)
    list_of_results[2] = new_element
    a = CZParametrisationFixDurationAnalysis()
    a.run_analysis_on_freq_amp_results(list_of_results)

    assert a.opt_index == 0
    assert a.opt_freq == (freqs[10] + freqs[9]) / 2
    assert a.opt_amp == (amps[12] + amps[13]) / 2
    assert a.opt_current == 0.1
