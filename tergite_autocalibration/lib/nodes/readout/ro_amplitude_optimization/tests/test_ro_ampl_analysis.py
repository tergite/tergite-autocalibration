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

import pytest
import xarray as xr

from tergite_autocalibration.lib.base.utils.analysis_utils import filter_ds_by_element
from tergite_autocalibration.lib.nodes.readout.ro_amplitude_optimization.analysis import (
    ROThreeStateAmplitudeNodeAnalysis,
    ROThreeStateAmplitudeQubitAnalysis,
)
from tergite_autocalibration.tests.utils.decorators import with_redis

_test_data_dir = os.path.join(
    Path(__file__).parent.parent.parent.parent, "data", "single-qubits-run"
)
_redis_values = os.path.join(_test_data_dir, "redis-single-qubits-run.json")


@with_redis(_redis_values)
def test_ro_ampl_3states():
    name = "ro_amplitude_three_state_optimization"
    file_path = os.path.join(_test_data_dir, name, f"dataset_{name}.hdf5")
    full_dataset = xr.open_dataset(file_path)
    qubit_qois = [
        "measure_3state_opt:pulse_amp",
        "centroid_I",
        "centroid_Q",
        "omega_01",
        "omega_12",
        "omega_20",
        "inv_cm_opt",
    ]

    ds_13 = filter_ds_by_element(full_dataset, "q13")
    ds_15 = filter_ds_by_element(full_dataset, "q15")

    analysis = ROThreeStateAmplitudeQubitAnalysis(name, qubit_qois)
    analysis.S21 = ds_13.isel(ReIm=0) + 1j * ds_13.isel(ReIm=1)
    analysis.data_var = "yq13"
    qoi = analysis.analyse_qubit()

    pulse_amp = qoi.analysis_result["measure_3state_opt:pulse_amp"]["value"]
    centroid_I = qoi.analysis_result["centroid_I"]["value"]
    centroid_Q = qoi.analysis_result["centroid_Q"]["value"]
    omega_01 = qoi.analysis_result["omega_01"]["value"]
    omega_12 = qoi.analysis_result["omega_12"]["value"]
    omega_20 = qoi.analysis_result["omega_20"]["value"]

    assert qoi.analysis_successful
    assert pytest.approx(pulse_amp) == 0.04369655
    assert pytest.approx(centroid_I) == -0.0166358284
    assert pytest.approx(centroid_Q) == 0.01054417388
    assert pytest.approx(omega_01) == 48.533332544
    assert pytest.approx(omega_12) == 289.04966963
    assert pytest.approx(omega_20) == 158.9517810

    analysis.S21 = ds_15.isel(ReIm=0) + 1j * ds_15.isel(ReIm=1)
    analysis.data_var = "yq15"
    qoi = analysis.analyse_qubit()

    pulse_amp = qoi.analysis_result["measure_3state_opt:pulse_amp"]["value"]
    centroid_I = qoi.analysis_result["centroid_I"]["value"]
    centroid_Q = qoi.analysis_result["centroid_Q"]["value"]
    omega_01 = qoi.analysis_result["omega_01"]["value"]
    omega_12 = qoi.analysis_result["omega_12"]["value"]
    omega_20 = qoi.analysis_result["omega_20"]["value"]

    assert qoi.analysis_successful
    assert pytest.approx(pulse_amp) == 0.0403862069
    assert pytest.approx(centroid_I) == 0.01131925
    assert pytest.approx(centroid_Q) == 0.01364486
    assert pytest.approx(omega_01) == 274.3834996
    assert pytest.approx(omega_12) == 156.0215330
    assert pytest.approx(omega_20) == 10.16925296


@with_redis(_redis_values)
def test_plotting():
    """
    Test that the plotter produces a figure with the right number of axes
    """
    name = "ro_amplitude_three_state_optimization"
    file_path = os.path.join(_test_data_dir, name)
    qubit_qois = [
        "measure_3state_opt:pulse_amp",
        "centroid_I",
        "centroid_Q",
        "omega_01",
        "omega_12",
        "omega_20",
        "inv_cm_opt",
    ]

    analysis = ROThreeStateAmplitudeNodeAnalysis(name, qubit_qois)
    analysis.analyze_node(file_path)
    number_of_qubits = len(analysis.dataset.attrs["elements"])
    assert analysis.axs.shape == (3, number_of_qubits)
