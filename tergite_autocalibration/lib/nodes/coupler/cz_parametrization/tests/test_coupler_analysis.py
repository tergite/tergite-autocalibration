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

from pathlib import Path

import pytest
import xarray as xr
from numpy import ndarray

from tergite_autocalibration.lib.base.analysis import (
    BaseAnalysis,
    BaseCouplerAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrization.analysis import (
    CZParametrisationFixDurationCouplerAnalysis,
    CombinedFrequencyVsAmplitudeAnalysis,
    FrequencyVsAmplitudeQ1Analysis,
    FrequencyVsAmplitudeQ2Analysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrization.utils.no_valid_combination_exception import (
    NoValidCombinationException,
)
from tergite_autocalibration.utils.logging import logger


def test_CanCreate():
    dataset_path = Path(__file__).parent / "data" / "dataset_good_quality_freq_amp.hdf5"
    ds = xr.open_dataset(dataset_path, engine="scipy")
    a = CZParametrisationFixDurationCouplerAnalysis("name", ["redis_field"])
    assert isinstance(a, CZParametrisationFixDurationCouplerAnalysis)
    assert isinstance(a, BaseCouplerAnalysis)
    assert isinstance(a, BaseAnalysis)


@pytest.fixture(autouse=True)
def setup_data():
    # It should be a single dataset, but we do not have one yet, so we loop over existing files
    dataset_path = Path(__file__).parent / "data" / "dataset_good_quality_freq_amp.hdf5"
    ds = xr.open_dataset(dataset_path, engine="scipy")
    d14 = ds["yq14"].to_dataset()
    d15 = ds["yq15"].to_dataset()
    d14.yq14.attrs["qubit"] = "q14"
    d15.yq15.attrs["qubit"] = "q15"
    freqs = ds[f"cz_pulse_frequenciesq14_q15"].values  # MHz
    amps = ds[f"cz_pulse_amplitudesq14_q15"].values  # uA
    q14Ana = FrequencyVsAmplitudeQ1Analysis("name", ["redis_field"], freqs, amps)
    q14Res = q14Ana.process_qubit(d14, "yq14")
    q15Ana = FrequencyVsAmplitudeQ2Analysis("name", ["redis_field"], freqs, amps)
    q15Res = q15Ana.process_qubit(d15, "yq15")
    c1 = CombinedFrequencyVsAmplitudeAnalysis(q14Res, q15Res)

    dataset_path = Path(__file__).parent / "data" / "dataset_bad_quality_freq_amp.hdf5"
    ds = xr.open_dataset(dataset_path, engine="scipy")
    d14 = ds["yq14"].to_dataset()
    d15 = ds["yq15"].to_dataset()
    d14.yq14.attrs["qubit"] = "q14"
    d15.yq15.attrs["qubit"] = "q15"
    freqs_bad = ds[f"cz_pulse_frequenciesq14_q15"].values  # MHz
    amps_bad = ds[f"cz_pulse_amplitudesq14_q15"].values  # uA
    q14Ana = FrequencyVsAmplitudeQ1Analysis("name", ["redis_field"], freqs, amps)
    q14Res = q14Ana.process_qubit(d14, "yq14")
    q15Ana = FrequencyVsAmplitudeQ2Analysis("name", ["redis_field"], freqs, amps)
    q15Res = q15Ana.process_qubit(d15, "yq15")
    c2 = CombinedFrequencyVsAmplitudeAnalysis(q14Res, q15Res)

    dataset_path = (
        Path(__file__).parent / "data" / "dataset_good_quality_freq_amp_2.hdf5"
    )
    ds = xr.open_dataset(dataset_path)
    d14 = ds["yq14"].to_dataset()
    d15 = ds["yq15"].to_dataset()
    d14.yq14.attrs["qubit"] = "q14"
    d15.yq15.attrs["qubit"] = "q15"
    freqs_2 = ds[f"cz_pulse_frequenciesq14_q15"].values  # MHz
    amps_2 = ds[f"cz_pulse_amplitudesq14_q15"].values  # uA
    c14 = FrequencyVsAmplitudeQ1Analysis("name", ["redis_field"], freqs_2, amps_2)
    q14Res = c14.process_qubit(d14, "yq14")
    c15 = FrequencyVsAmplitudeQ2Analysis("name", ["redis_field"], freqs_2, amps_2)
    q15Res = c15.process_qubit(d15, "yq15")
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
    ],
):
    ds, list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    a = CZParametrisationFixDurationCouplerAnalysis("name", ["redis_fields"])
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
    ],
):
    ds, list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    logger.info(list_of_results[2][0])
    list_of_results.pop(0)
    a = CZParametrisationFixDurationCouplerAnalysis("name", ["redis_fields"])
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
    ],
):
    ds, list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    logger.info(len(list_of_results))
    list_of_results.pop(2)
    list_of_results.pop(0)
    a = CZParametrisationFixDurationCouplerAnalysis("name", ["redis_fields"])

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
    ],
):
    ds, list_of_results, freqs, amps, freqs_2, amps_2 = setup_data
    logger.info(len(list_of_results))
    new_element = (list_of_results[2][0], -0.3)
    list_of_results[2] = new_element
    a = CZParametrisationFixDurationCouplerAnalysis("name", ["redis_fields"])
    a.run_analysis_on_freq_amp_results(list_of_results)

    assert a.opt_index == 0
    assert a.opt_freq == (freqs[10] + freqs[9]) / 2
    assert a.opt_amp == (amps[12] + amps[13]) / 2
    assert a.opt_current == 0.1


@pytest.fixture(autouse=True)
def setup_data_mutliple_files():
    # It should be a single dataset, but we do not have one yet, so we loop over existing files
    dataset_path = (
        Path(__file__).parent
        / "data"
        / "dataset_cz_parametrization_fix_duration_0.hdf5"
    )
    ds = xr.open_dataset(dataset_path, engine="scipy")
    combined_dataset = ds

    # combined_dataset = xr.Dataset()
    for i in (1, 2, 3):
        filename = "dataset_cz_parametrization_fix_duration_" + str(i) + ".hdf5"
        dataset_path = Path(__file__).parent / "data" / filename
        ds = xr.open_dataset(dataset_path, engine="scipy")
        combined_dataset = xr.merge([combined_dataset, ds])

    freqs = ds[f"cz_pulse_frequenciesq06_q07"].values  # MHz
    amps = ds[f"cz_pulse_amplitudesq06_q07"].values  # uA
    currents = combined_dataset[f"cz_parking_currentsq06_q07"].values
    logger.info(combined_dataset)

    return combined_dataset, freqs, amps
