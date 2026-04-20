# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou  2026
# (C) Chalmers Next Labs AB 2026
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

import numpy as np
import pytest
import xarray as xr

from tergite_autocalibration.lib.base.utils.analysis_utils import filter_ds_by_element
from tergite_autocalibration.lib.nodes.qubit_control.motzoi_parameter.analysis import (
    Motzoi01NodeAnalysis,
    Motzoi01QubitAnalysis,
)
from tergite_autocalibration.tests.utils.decorators import with_redis

_test_data_dir = os.path.join(
    Path(__file__).parent.parent.parent.parent, "data", "single_qubits_run"
)
_redis_values = os.path.join(_test_data_dir, "redis-single-qubits-run.json")


@with_redis(_redis_values)
def test_motzoi_parameter():
    name = "motzoi_parameter"
    file_path = os.path.join(_test_data_dir, name, f"dataset_{name}.hdf5")
    full_dataset = xr.open_dataset(file_path)
    qubit_qois = ["rxy:motzoi"]

    ds_13 = filter_ds_by_element(full_dataset, "q13")
    ds_15 = filter_ds_by_element(full_dataset, "q15")

    analysis = Motzoi01QubitAnalysis(name, qubit_qois)
    s21 = ds_13.isel(ReIm=0) + 1j * ds_13.isel(ReIm=1)
    analysis.magnitudes = np.abs(s21)
    analysis.data_var = "yq13"
    qoi = analysis.analyse_qubit()

    motzoi_01 = qoi.analysis_result["rxy:motzoi"]["value"]

    assert qoi.analysis_successful
    assert pytest.approx(motzoi_01) == 0.023076923077

    s21 = ds_15.isel(ReIm=0) + 1j * ds_15.isel(ReIm=1)
    analysis.magnitudes = np.abs(s21)
    analysis.data_var = "yq15"
    qoi = analysis.analyse_qubit()

    motzoi_01 = qoi.analysis_result["rxy:motzoi"]["value"]

    assert qoi.analysis_successful
    assert pytest.approx(motzoi_01) == -0.0923076923077


@with_redis(_redis_values)
def test_plotting():
    """
    Test that the plotter produces a figure with the right number of axes
    """
    name = "motzoi_parameter"
    file_path = os.path.join(_test_data_dir, name)
    qubit_qois = ["rxy:motzoi"]

    analysis = Motzoi01NodeAnalysis(name, qubit_qois)
    analysis.analyze_node(file_path)
    number_of_qubits = len(analysis.dataset.attrs["elements"])
    assert analysis.axs.shape == (1, number_of_qubits)
