# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from tergite_autocalibration.tests.utils.env import setup_test_env

setup_test_env()

from pathlib import Path

import pytest
import xarray as xr
from numpy import ndarray

from tergite_autocalibration.lib.base.analysis import BaseAnalysis
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.analysis import (
    CZParametrisationFixDurationAnalysis,
    CombinedFrequencyVsAmplitudeAnalysis,
    FrequencyVsAmplitudeQ1Analysis,
    FrequencyVsAmplitudeQ2Analysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.utils.no_valid_combination_exception import (
    NoValidCombinationException,
)


def test_CanCreate():
    dataset_path = Path(__file__).parent / "data" / "dataset_good_quality_freq_amp.hdf5"
    ds = xr.open_dataset(dataset_path)
    a = CZParametrisationFixDurationAnalysis(ds)
    assert isinstance(a, CZParametrisationFixDurationAnalysis)
    assert isinstance(a, BaseAnalysis)


@pytest.fixture(autouse=True)
def setup_data():
    # It should be a single dataset, but we do not have one yet, so we loop over existing files
    dataset_path = Path(__file__).parent / "data" / "dataset_good_quality_freq_amp.hdf5"
    ds = xr.open_dataset(dataset_path)

    freqs = ds[f"cz_pulse_frequenciesq14_q15"].values  # MHz
    amps = ds[f"cz_pulse_amplitudesq14_q15"].values  # uA
    q14Ana = FrequencyVsAmplitudeQ1Analysis(ds, freqs, amps)
    q14Res = q14Ana.analyse_qubit()
    q15Ana = FrequencyVsAmplitudeQ2Analysis(ds, freqs, amps)
    q15Res = q15Ana.analyse_qubit()
    c1 = CombinedFrequencyVsAmplitudeAnalysis(q14Res, q15Res)

    dataset_path = Path(__file__).parent / "data" / "dataset_bad_quality_freq_amp.hdf5"
    ds = xr.open_dataset(dataset_path)

    freqs_bad = ds[f"cz_pulse_frequenciesq14_q15"].values  # MHz
    amps_bad = ds[f"cz_pulse_amplitudesq14_q15"].values  # uA
    q14Ana = FrequencyVsAmplitudeQ1Analysis(ds, freqs_bad, amps_bad)
    q14Res = q14Ana.analyse_qubit()
    q15Ana = FrequencyVsAmplitudeQ2Analysis(ds, freqs_bad, amps_bad)
    q15Res = q15Ana.analyse_qubit()
    c2 = CombinedFrequencyVsAmplitudeAnalysis(q14Res, q15Res)

    dataset_path = (
        Path(__file__).parent / "data" / "dataset_good_quality_freq_amp_2.hdf5"
    )
    ds = xr.open_dataset(dataset_path)

    freqs_2 = ds[f"cz_pulse_frequenciesq14_q15"].values  # MHz
    amps_2 = ds[f"cz_pulse_amplitudesq14_q15"].values  # uA
    q14Ana = FrequencyVsAmplitudeQ1Analysis(ds, freqs_2, amps_2)
    q14Res = q14Ana.analyse_qubit()
    q15Ana = FrequencyVsAmplitudeQ2Analysis(ds, freqs_2, amps_2)
    q15Res = q15Ana.analyse_qubit()
    c3 = CombinedFrequencyVsAmplitudeAnalysis(q14Res, q15Res)

    list_of_results = [(c1, 0.1), (c2, 0.2), (c3, 0.3)]
    return ds, list_of_results, freqs, amps, freqs_2, amps_2


def test_PickLowestCurrent(
    setup_data: tuple[
        list[xr.Dataset, tuple[CombinedFrequencyVsAmplitudeAnalysis, float]],
        ndarray,
        ndarray,
        ndarray,
        ndarray,
    ]
):
    ds, list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    a = CZParametrisationFixDurationAnalysis(ds)
    a.run_analysis_on_freq_amp_results(list_of_results)

    assert a.opt_index == 0
    assert a.opt_freq == (freqs[10] + freqs[9]) / 2
    assert a.opt_amp == (amps[12] + amps[13]) / 2
    assert a.opt_current == 0.1


def test_PickLowestCurrentWithoutBest(
    setup_data: tuple[
        xr.Dataset,
        list[tuple[CombinedFrequencyVsAmplitudeAnalysis, float]],
        ndarray,
        ndarray,
        ndarray,
        ndarray,
    ]
):
    ds, list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    list_of_results.pop(0)
    a = CZParametrisationFixDurationAnalysis(ds)
    a.run_analysis_on_freq_amp_results(list_of_results)

    assert (
        a.opt_index == 1
    )  # I removed the first, so the good point is now the last which is in position 1
    assert a.opt_freq == freqs_2[5]
    assert a.opt_amp == amps_2[10]
    assert a.opt_current == 0.3


def test_ReturnErrorIfNoGoodPoint(
    setup_data: tuple[
        xr.Dataset,
        list[tuple[CombinedFrequencyVsAmplitudeAnalysis, float]],
        ndarray,
        ndarray,
        ndarray,
        ndarray,
    ]
):
    ds, list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    print(len(list_of_results))
    list_of_results.pop(2)
    list_of_results.pop(0)
    a = CZParametrisationFixDurationAnalysis(ds)

    with pytest.raises(NoValidCombinationException, match="No valid combination found"):
        a.run_analysis_on_freq_amp_results(list_of_results)


def test_PickGoodValueIfSmallestInAbsolute(
    setup_data: tuple[
        xr.Dataset,
        list[tuple[CombinedFrequencyVsAmplitudeAnalysis, float]],
        ndarray,
        ndarray,
        ndarray,
        ndarray,
    ]
):
    ds, list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    print(len(list_of_results))
    new_element = (list_of_results[2][0], -0.3)
    list_of_results[2] = new_element
    a = CZParametrisationFixDurationAnalysis(ds)
    a.run_analysis_on_freq_amp_results(list_of_results)

    assert a.opt_index == 0
    assert a.opt_freq == (freqs[10] + freqs[9]) / 2
    assert a.opt_amp == (amps[12] + amps[13]) / 2
    assert a.opt_current == 0.1


@pytest.fixture(autouse=True)
def setup_data_mutliple_files():
    # It should be a single dataset, but we do not have one yet, so we loop over existing files
    dataset_path = Path(__file__).parent / "data" / "dataset_fix_time_0.hdf5"
    ds = xr.open_dataset(dataset_path)
    combined_dataset = ds

    combined_dataset = xr.Dataset()
    for i in (1, 2, 3):
        filename = "dataset_fix_time_" + str(i) + ".hdf5"
        dataset_path = Path(__file__).parent / "data" / filename
        ds = xr.open_dataset(dataset_path)
        combined_dataset = xr.merge([combined_dataset, ds])

    freqs = ds[f"cz_pulse_frequenciesq06_q07"].values  # MHz
    amps = ds[f"cz_pulse_amplitudesq06_q07"].values  # uA
    currents = combined_dataset[f"cz_parking_currentsq06_q07"].values
    print(combined_dataset)

    return combined_dataset, freqs, amps


def test_PickLowestCurrentCompleteAnalysis(
    setup_data_mutliple_files: tuple[xr.Dataset, ndarray, ndarray]
):
    ds, freqs, amps = setup_data_mutliple_files
    a = CZParametrisationFixDurationAnalysis(ds)
    a.analyse_qubit()

    assert a.opt_index == 0
    assert a.opt_freq == (freqs[10] + freqs[9]) / 2
    assert a.opt_amp == (amps[12] + amps[13]) / 2
    assert a.opt_current == 0.1
