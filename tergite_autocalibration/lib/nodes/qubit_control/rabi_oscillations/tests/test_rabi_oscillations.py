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
import xarray as xr

from tergite_autocalibration.lib.nodes.qubit_control.rabi_oscillations.analysis import (
    Rabi12QubitAnalysis,
    RabiQubitAnalysis,
)
from tergite_autocalibration.utils.dto.qoi import QOI


class TestRabiQubitAnalysis(unittest.TestCase):
    def test_setup_01(self):
        test_dir = Path(__file__).parent
        file_path = test_dir / "data_rabi_01" / "dataset_rabi_oscillations_0.hdf5"
        dataset = xr.open_dataset(file_path)
        analysis = RabiQubitAnalysis("name", ["rxy:amp180"])

        qoi = analysis.process_qubit(dataset, "yq06")
        result_values = qoi.analysis_result
        self.assertIsInstance(qoi, QOI)
        for quantity in result_values:
            self.assertIsInstance(result_values[quantity]["value"], float)
        assert (
            len(result_values) == 1
        ), f"The dataset should contain one element {len(dataset)}"

    def test_setup_12(self):
        test_dir = Path(__file__).parent
        file_path = test_dir / "data_rabi_12" / "dataset_rabi_oscillations_12_0.hdf5"
        dataset = xr.open_dataset(file_path)
        analysis = Rabi12QubitAnalysis("name", ["r12:ef_amp180"])

        qoi = analysis.process_qubit(dataset, "yq06")
        result_values = qoi.analysis_result
        self.assertIsInstance(qoi, QOI)
        for quantity in result_values:
            self.assertIsInstance(result_values[quantity]["value"], float)
        assert (
            len(result_values) == 1
        ), f"The dataset should contain one element {len(dataset)}"

    def test_run_fitting_01(self):
        test_dir = Path(__file__).parent
        file_path = test_dir / "data_rabi_01" / "dataset_rabi_oscillations_0.hdf5"
        dataset = xr.open_dataset(file_path)
        analysis = RabiQubitAnalysis("name", ["rxy:amp180"])
        qoi = analysis.process_qubit(dataset, "yq06")
        amplitude = qoi.analysis_result["rxy:amp180"]["value"]

        assert amplitude > 0, "Amplitude has to be higher than 0"

    def test_run_fitting_12(self):
        test_dir = Path(__file__).parent
        file_path = test_dir / "data_rabi_12" / "dataset_rabi_oscillations_12_0.hdf5"
        dataset = xr.open_dataset(file_path)
        analysis = Rabi12QubitAnalysis("name", ["r12:ef_amp180"])
        qoi = analysis.process_qubit(dataset, "yq06")
        amplitude = qoi.analysis_result["r12:ef_amp180"]["value"]

        assert amplitude > 0, f"Amplitude has to be higher than 0: {amplitude}"

    def test_plotting_01(self):
        os.environ["DATA_DIR"] = str(Path(__file__).parent / "results")
        test_dir = Path(__file__).parent
        file_path = test_dir / "data_rabi_01" / "dataset_rabi_oscillations_0.hdf5"
        dataset = xr.open_dataset(file_path)
        analysis = RabiQubitAnalysis("name", ["rxy:amp180"])
        analysis.process_qubit(dataset, "yq06")
        figure_path = os.environ["DATA_DIR"] + "/Rabi_oscillations_01_q06.png"
        if os.path.exists(figure_path):
            os.remove(figure_path)
        fig, ax = plt.subplots()
        analysis.plotter(ax)
        fig.savefig(figure_path)
        plt.close(fig)
        assert os.path.exists(
            figure_path
        ), f"Expected plot file to be created at {figure_path}"

    def test_plotting_12(self):
        os.environ["DATA_DIR"] = str(Path(__file__).parent / "results")
        test_dir = Path(__file__).parent
        file_path = test_dir / "data_rabi_12" / "dataset_rabi_oscillations_12_0.hdf5"
        file = xr.open_dataset(file_path)
        analysis = Rabi12QubitAnalysis("name", ["r12:ef_amp180"])
        analysis.process_qubit(file, "yq06")
        figure_path = os.environ["DATA_DIR"] + "/Rabi_oscillations_12_q06.png"
        if os.path.exists(figure_path):
            os.remove(figure_path)
        fig, ax = plt.subplots()
        analysis.plotter(ax)
        fig.savefig(figure_path)
        plt.close(fig)
        assert os.path.exists(
            figure_path
        ), f"Expected plot file to be created at {figure_path}"
