from pathlib import Path

import pytest
from tergite_autocalibration.lib.base.analysis import BaseAnalysis
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.CZ_Parametrisation_Combined_Frequency_vs_Amplitude_Analysis import (
    CZ_Parametrisation_Combined_Frequency_vs_Amplitude_Analysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis import (
    CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis import (
    CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.analysis import (
    CZ_Parametrisation_Fix_Duration_Analysis,
)
import xarray as xr

from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.utils.NoValidCombinationException import (
    NoValidCombinationException,
)


def test_CanCreate():
    a = CZ_Parametrisation_Fix_Duration_Analysis()
    assert isinstance(a, CZ_Parametrisation_Fix_Duration_Analysis)
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
    q14Ana = CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis(d14, freqs, amps)
    q14Res = q14Ana.run_fitting()
    q15Ana = CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis(d15, freqs, amps)
    q15Res = q15Ana.run_fitting()
    c1 = CZ_Parametrisation_Combined_Frequency_vs_Amplitude_Analysis(q14Res, q15Res)

    dataset_path = Path(__file__).parent / "data" / "dataset_bad_quality_freq_amp.hdf5"
    print(dataset_path)
    ds = xr.open_dataset(dataset_path)
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d14 = ds.yq14.to_dataset()
    d15 = ds.yq15.to_dataset()
    d14.yq14.attrs["qubit"] = "q14"
    d15.yq15.attrs["qubit"] = "q15"
    freqs_bad = ds[f"cz_pulse_frequenciesq14_q15"].values  # MHz
    amps_bad = ds[f"cz_pulse_amplitudesq14_q15"].values  # uA
    q14Ana = CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis(
        d14, freqs_bad, amps_bad
    )
    q14Res = q14Ana.run_fitting()
    q15Ana = CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis(
        d15, freqs_bad, amps_bad
    )
    q15Res = q15Ana.run_fitting()
    c2 = CZ_Parametrisation_Combined_Frequency_vs_Amplitude_Analysis(q14Res, q15Res)

    dataset_path = (
        Path(__file__).parent / "data" / "dataset_good_quality_freq_amp_2.hdf5"
    )
    print(dataset_path)
    ds = xr.open_dataset(dataset_path)
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d14 = ds.yq14.to_dataset()
    d15 = ds.yq15.to_dataset()
    d14.yq14.attrs["qubit"] = "q14"
    d15.yq15.attrs["qubit"] = "q15"
    freqs_2 = ds[f"cz_pulse_frequenciesq14_q15"].values  # MHz
    amps_2 = ds[f"cz_pulse_amplitudesq14_q15"].values  # uA
    q14Ana = CZ_Parametrisation_Frequency_vs_Amplitude_Q1_Analysis(d14, freqs_2, amps_2)
    q14Res = q14Ana.run_fitting()
    q15Ana = CZ_Parametrisation_Frequency_vs_Amplitude_Q2_Analysis(d15, freqs_2, amps_2)
    q15Res = q15Ana.run_fitting()
    c3 = CZ_Parametrisation_Combined_Frequency_vs_Amplitude_Analysis(q14Res, q15Res)

    list_of_results = [(c1, 0.1), (c2, 0.2), (c3, 0.3)]
    return list_of_results, freqs, amps, freqs_2, amps_2


def test_PickLowestCurrent(setup_data):
    list_of_results, freqs, amps = setup_data
    a = CZ_Parametrisation_Fix_Duration_Analysis()
    a.run_analysis_on_freq_amp_results(list_of_results)

    assert a.opt_index == 0
    assert a.opt_freq == (freqs[10] + freqs[9]) / 2
    assert a.opt_amp == (amps[12] + amps[13]) / 2
    assert a.opt_current == 0.1


def test_PickLowestCurrentWithoutBest(setup_data):
    list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    list_of_results.pop(0)
    a = CZ_Parametrisation_Fix_Duration_Analysis()
    a.run_analysis_on_freq_amp_results(list_of_results)

    assert (
        a.opt_index == 1
    )  # I removed the first, so the good point is now the last which is in position 1
    assert a.opt_freq == freqs_2[5]
    assert a.opt_amp == amps_2[10]
    assert a.opt_current == 0.3


def test_ReturnErrorIfNoGoodPoint(setup_data):
    list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    print(len(list_of_results))
    list_of_results.pop(2)
    list_of_results.pop(0)
    a = CZ_Parametrisation_Fix_Duration_Analysis()

    with pytest.raises(NoValidCombinationException, match="No valid combination found"):
        a.run_analysis_on_freq_amp_results(list_of_results)
