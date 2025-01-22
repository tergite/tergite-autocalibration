# This code is part of Tergite
#
# (C) Copyright Joel Sandås 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os
import unittest
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
import xarray as xr

from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.analysis import (
    ResonatorSpectroscopyQubitAnalysis,
)
from tergite_autocalibration.utils.dto.qoi import QOI


class TestResonatorFrequencyAnalysis(unittest.TestCase):
    def test_setup(self):
        test_dir = Path(__file__).parent
        file_path = test_dir / "data_0" / "dataset_resonator_spectroscopy_0.hdf5"
        dataset = xr.open_dataset(file_path)
        analysis = ResonatorSpectroscopyQubitAnalysis(
            "name", ["clock_freqs:readout", "Ql", "resonator_minimum"]
        )
        qoi = analysis.process_qubit(dataset, "yq06")
        result_values = qoi.analysis_result

        self.assertIsInstance(qoi, QOI)
        for quantity in result_values:
            self.assertIsInstance(result_values[quantity]["value"], np.float64)
        assert (
            len(result_values) == 3
        ), f"The dataset should contain three elements {len(dataset)}"

    def test_run_fitting(self):
        test_dir = Path(__file__).parent
        file_path = test_dir / "data_0" / "dataset_resonator_spectroscopy_0.hdf5"
        dataset = xr.open_dataset(file_path)
        analysis = ResonatorSpectroscopyQubitAnalysis(
            "name", ["clock_freqs:readout", "Ql", "resonator_minimum"]
        )
        qoi = analysis.process_qubit(dataset, "yq06")
        minimum_freq = qoi.analysis_result["clock_freqs:readout"]["value"]
        fit_Ql = qoi.analysis_result["Ql"]["value"]
        min_freq_data = qoi.analysis_result["resonator_minimum"]["value"]

        assert (
            6e9 < minimum_freq < 8e9
        ), f"Minimum frequency should be between 6 GHz and 8 GHz, got {minimum_freq}"
        assert fit_Ql > 0, f"Fit Ql should be a positive value, got {fit_Ql}"
        assert min_freq_data == pytest.approx(
            minimum_freq, rel=1e3
        ), f"The both frequencies should be close to each other {minimum_freq} {min_freq_data}"

    def test_plotting(self):
        os.environ["DATA_DIR"] = str(Path(__file__).parent / "results")
        test_dir = Path(__file__).parent
        file_path = test_dir / "data_0" / "dataset_resonator_spectroscopy_0.hdf5"
        dataset = xr.open_dataset(file_path)
        analysis = ResonatorSpectroscopyQubitAnalysis(
            "name", ["clock_freqs:readout", "Ql", "resonator_minimum"]
        )
        dataset = analysis.process_qubit(dataset, "yq06")
        figure_path = os.environ["DATA_DIR"] + "/Resonator_spectroscopy_q06.png"
        if os.path.exists(figure_path):
            os.remove(figure_path)

        fig, ax = plt.subplots()
        analysis.plotter(ax)
        fig.savefig(figure_path)
        plt.close(fig)
