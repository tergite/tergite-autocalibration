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

from tergite_autocalibration.tests.utils.env import setup_test_env

setup_test_env()

from pathlib import Path
import os
import pytest
import unittest
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.analysis import QubitSpectroscopyMultidim

class TestResonatorFrequencyAnalysis(unittest.TestCase):

    def test_setup(self):
        test_dir = Path(__file__).parent
        file_path = test_dir / "data_01" / "dataset_qubit_01_spectroscopy_0.hdf5"
        file = xr.open_dataset(file_path)
        analysis = QubitSpectroscopyMultidim("name", ["redis_field"])
        dataset = analysis.process_qubit(file, "yq06")

        self.assertIsInstance(dataset, list)
        for i in dataset:
            self.assertIsInstance(i, np.float64)
        assert len(dataset) == 2, f"The dataset should contain two elements {len(dataset)}"

    def test_run_fitting(self):
        test_dir = Path(__file__).parent
        file_path = test_dir / "data_01" / "dataset_qubit_01_spectroscopy_0.hdf5"
        file = xr.open_dataset(file_path)
        analysis = QubitSpectroscopyMultidim("name", ["redis_field"])
        dataset = analysis.process_qubit(file, "yq06")
        frequency = dataset[0]
        ampl = dataset[1]

        assert 4e9 < frequency < 6e9, f"Frequency should be between 4 GHz and 6 GHz, got {frequency}"
        assert ampl > 0, f"Amplitude has to be higher than 0"

    def test_plotting(self):
        os.environ["DATA_DIR"] = str(Path(__file__).parent / "results")
        test_dir = Path(__file__).parent
        file_path = test_dir / "data_01" / "dataset_qubit_01_spectroscopy_0.hdf5"
        file = xr.open_dataset(file_path)
        analysis = QubitSpectroscopyMultidim("name", ["redis_field"])
        dataset = analysis.process_qubit(file, "yq06")
        figure_path = os.environ["DATA_DIR"] + "/Qubit_spectroscopy_q06.png"
        if os.path.exists(figure_path):
            os.remove(figure_path)
        fig, ax = plt.subplots()
        analysis.plotter(ax)
        fig.savefig(figure_path)
        plt.close(fig)
        assert os.path.exists(figure_path), f"Expected plot file to be created at {figure_path}"
        