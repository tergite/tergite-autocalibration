# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2025
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import collections
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import cf_xarray as cf

# TODO: we should have a conditional import depending on a feature flag here
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.utils.figure_utils import (
    create_figure_with_top_band,
)
from tergite_autocalibration.utils.dto.qoi import QOI
from tergite_autocalibration.utils.logging import logger


class BaseAnalysis(ABC):
    """
    Base class for the analysis
    """

    def __init__(self):
        self._qoi = None
        self.redis_fields = ""
        self.dataset: xr.Dataset
        self.S21: xr.DataArray
        self.magnitudes: xr.DataArray
        self.data_var = None
        self.qubit: str
        self.coord = None
        self.data_path = ""

    @property
    def qoi(self) -> "QOI":
        return self._qoi

    @qoi.setter
    def qoi(self, value: "QOI"):
        self._qoi = value

    @abstractmethod
    def plotter(self) -> None:
        """
        Plot the fitted values from the analysis

        Returns:
            None: This will just plot the fitted values

        """


class BaseNodeAnalysis(ABC):
    """
    Base class for the analysis
    """

    def __init__(self):
        self.name = ""
        self._qoi = None
        self.redis_fields = ""
        self.name = ""
        self.data_path = None
        self.dataset = None
        self.data_vars = None
        self.coords = None
        self.fig = None
        self.axs = None

    @property
    def qoi(self) -> "QOI":
        return self._qoi

    @qoi.setter
    def qoi(self, value: "QOI"):
        self._qoi = value

    @abstractmethod
    def analyze_node(self, data_path: Path) -> dict[str, QOI]:
        """
        Run the fitting of the analysis function

        Returns:
            The quantity of interest as QOI wrapped object

        """

    def open_dataset(self) -> xr.Dataset:
        """
        Open the dataset for the analysis.

        Args:

        Returns:
            xarray.Dataset with measurement results

        """
        dataset_name = f"dataset_{self.name}.hdf5"
        dataset_path = os.path.join(self.data_path, dataset_name)
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

        logger.info("Open dataset " + str(dataset_path))
        dataset = xr.open_dataset(dataset_path)
        if "working_points" in dataset.coords:
            dataset = cf.decode_compress_to_multi_index(dataset, "working_points")
        return dataset

    # def save_processed_dataset(self):
    #     dataset_name = f"dataset_{self.name}_processed.hdf5"
    #     if "working_points" in self.processed_dataset.coords:
    #         self.processed_dataset = cf.encode_multi_index_as_compress(
    #             self.processed_dataset, "working_points"
    #         )
    #     self.processed_dataset.to_netcdf(self.data_path / dataset_name)

    def _manage_plots(self, column_grid: int, plots_per_qubit: int):
        n_vars = len(self.data_vars)
        nrows = int(np.ceil(n_vars / column_grid)) * plots_per_qubit
        ncols = min(column_grid, n_vars)

        fig, axs = create_figure_with_top_band(nrows, ncols)

        return fig, axs

    def _save_plots(self):
        preview_path = self.data_path / f"{self.name}_preview.png"
        full_path = self.data_path / f"{self.name}.png"
        logger.info("Saving Plots")
        self.fig.savefig(preview_path, bbox_inches="tight", dpi=100)
        self.fig.savefig(full_path, bbox_inches="tight", dpi=400)
        logger.info(f"Plots saved to {preview_path} and {full_path}")

    def _save_other_plots(self):
        pass


class BaseAllQubitsAnalysis(BaseNodeAnalysis, ABC):
    """
    Base class for the analysis of all qubits in a node
    """

    single_qubit_analysis_obj: "BaseQubitAnalysis"

    def __init__(self, name: str, redis_fields):
        super().__init__()
        self.name = name
        self.redis_fields = redis_fields
        self.dataset = None
        self.data_vars = None
        self.coords = None

        self.qubit_analyses: List[BaseQubitAnalysis] = []

        self.column_grid = 5
        self.plots_per_qubit = 1

    def analyze_node(self, data_path: Path) -> dict[str, QOI]:
        """
        Analyze the node and save the results to redis.
        Args:
            data_path: Path to the dataset

        Returns:
            analysis_results: Dictionary with the analysis results for each qubit
        """

        self.data_path = Path(data_path)
        self.dataset = self.open_dataset()
        self.coords = self.dataset.coords
        self.data_vars = self.dataset.data_vars
        self.fig, self.axs = self._manage_plots(self.column_grid, self.plots_per_qubit)
        analysis_results = self._analyze_all_qubits()
        self._fill_plots()
        self._save_plots()
        self._save_other_plots()
        return analysis_results

    def _analyze_all_qubits(self):
        analysis_results = {}
        qubit_data_dict = self._group_by_qubit()
        for this_qubit, qubit_data_vars in qubit_data_dict.items():
            ds = xr.merge([self.dataset[var] for var in qubit_data_vars])
            ds.attrs["qubit"] = this_qubit
            ds.attrs["node"] = self.name

            matching_coords = [coord for coord in ds.coords if this_qubit in coord]
            if matching_coords:
                selected_coord_name = matching_coords[0]
                ds = ds.sel(
                    {selected_coord_name: slice(None)}
                )  # Select all data along this coordinate

                qubit_analysis: BaseQubitAnalysis = self.single_qubit_analysis_obj(
                    self.name, self.redis_fields
                )
                # NOTE: coord initialization cannot be done in the __init__ because
                # the dataset is loaded by the process_qubit method.
                # in other words the __init__ of the analysis class is not aware of the
                # dataset to be analyzed
                analysis_results[this_qubit] = qubit_analysis.process_qubit(
                    ds, this_qubit
                )
                self.qubit_analyses.append(qubit_analysis)

        return analysis_results

    def _group_by_qubit(self):
        qubit_data_dict = collections.defaultdict(set)
        for var in self.dataset.data_vars:
            this_qubit = self.dataset[var].attrs["qubit"]
            qubit_data_dict[this_qubit].add(var)
        return qubit_data_dict

    def _fill_plots(self):
        for index, analysis in enumerate(self.qubit_analyses):
            primary_plot_row = self.plots_per_qubit * (index // self.column_grid)
            primary_axis = self.axs[primary_plot_row, index % self.column_grid]
            analysis.plot(primary_axis)


class BaseQubitAnalysis(BaseAnalysis, ABC):
    """
    Base class for the analysis of a single qubit
    """

    def __init__(self, name, redis_fields):
        super().__init__()
        self.name = name
        self.redis_fields = redis_fields

    def process_qubit(self, dataset, qubit_element) -> QOI:
        """
        Setup the qubit data and analyze it.
        Args:
            dataset: xarray dataset with the qubit data
            qubit_element: name of the qubit element
        Returns:
            QOI: Quantity of interest as QOI wrapped object
        """

        self.dataset = dataset
        self.qubit = qubit_element
        self._set_data_variables()
        self._compute_magnitudes()
        self._qoi = self.analyse_qubit()
        return self._qoi

    def _set_data_variables(self):
        self.coord = self.dataset.coords
        self.data_var = list(self.dataset.data_vars.keys())[0]

    def _compute_magnitudes(self):
        self.S21 = self.dataset.isel(ReIm=0) + 1j * self.dataset.isel(ReIm=1)
        self.magnitudes = np.abs(self.S21)

    def plot(self, primary_axis):
        """
        Plot the fitted values from the analysis
        Args:
            primary_axis: The axis object from matplotlib to be plotted
        Returns:
            None, will just plot the fitted values
        """

        self.plotter(primary_axis)  # Assuming node_analysis object is available
        primary_axis.set_title(f"Qubit {self.qubit}")

    @abstractmethod
    def analyse_qubit(self) -> QOI:
        """
        Run the actual analysis function

        Returns:
            The quantity of interest as QOI wrapped object

        """


class BaseCouplerAnalysis(BaseAnalysis, ABC):
    """
    Base class for the analysis of a single coupler
    """

    def __init__(self, name, redis_fields, **kwargs):
        super().__init__()
        self.name = name
        self.redis_fields = redis_fields
        self.dataset = None
        self.data_vars = None
        self.coords = None
        self.coupler = ""

    def qubit_types(self, coupler: str):
        control_qubit = REDIS_CONNECTION.hget(f"couplers:{coupler}", "control_qubit")
        target_qubit = REDIS_CONNECTION.hget(f"couplers:{coupler}", "target_qubit")
        return control_qubit, target_qubit

    def process_coupler(self, dataset: xr.Dataset, coupler_element) -> QOI:
        self.control_qubit, self.target_qubit = self.qubit_types(coupler_element)
        self.dataset = dataset
        self.coupler = coupler_element
        self.coord = dataset.coords
        self.data_var = list(dataset.data_vars.keys())[
            0
        ]  # Assume the first data_var is relevant
        self.S21 = dataset.isel(ReIm=0) + 1j * dataset.isel(ReIm=1)
        # Restore attributes for each variable
        for var in self.S21.data_vars:
            self.S21[var].attrs = dataset[var].attrs
        self.magnitudes = np.abs(self.S21)

        for var in self.S21.data_vars:
            data_var = self.S21[var]
            if data_var.attrs["qubit"] == self.control_qubit:
                self.control_qubit_data_var = data_var
            elif data_var.attrs["qubit"] == self.target_qubit:
                self.target_qubit_data_var = data_var
            else:
                raise ValueError

        self._qoi = self.analyze_coupler()

        return self._qoi

    @abstractmethod
    def analyze_coupler(self):
        pass


class BaseAllCouplersAnalysis(BaseNodeAnalysis, ABC):
    """
    Base class for the analysis of all couplers in a node
    """

    single_coupler_analysis_obj: "BaseCouplerAnalysis"

    def __init__(self, name, redis_fields, **kwargs):
        super().__init__()
        self.name = name
        self.redis_fields = redis_fields
        self.dataset: xr.Dataset
        self.data_vars = None
        self.coords = None

        self.figures_dictionary = {}
        self.processed_dataset = xr.Dataset()
        self.analysis_keywords = kwargs

    def analyze_node(self, data_path: Path) -> QOI:
        """
        Analyze the node and save the results to redis.
        Args:
            data_path: Path to the dataset
            index: Index of the dataset to be analyzed

        Returns:
            analysis_results: Dictionary with the analysis results for each qubit
        """

        self.data_path = Path(data_path)
        self.dataset = self.open_dataset()
        self.coords = self.dataset.coords
        self.data_vars = self.dataset.data_vars
        analysis_results = self._analyze_all_couplers()
        self.display_and_save_plots()
        return analysis_results

    def display_and_save_plots(self):
        # if the dictionary is empty do nothing
        if not self.figures_dictionary:
            return

        for coupler, figure_list in self.figures_dictionary.items():
            for fig_index, fig in enumerate(figure_list):
                preview_path = (
                    self.data_path / f"{self.name}_{coupler}_{fig_index}_preview.png"
                )
                # this corresponds to faceted plots
                if fig.axes[0].get_gridspec().get_geometry() == (2, 3):
                    fig.set_size_inches(14, 9)
                else:
                    nrows = fig.axes[0].get_gridspec().nrows
                    ncols = fig.axes[0].get_gridspec().ncols
                    if nrows == 1 and ncols == 1:
                        fig.set_size_inches(9, 6)
                    else:
                        fig.set_size_inches(ncols * 6, nrows * 4)

                fig.savefig(preview_path, bbox_inches="tight", dpi=100)
                # some slack for the figure x and y labels
                fig.tight_layout(rect=[0.05, 0.05, 1, 0.98])

    def _analyze_all_couplers(self):
        analysis_results = {}
        coupler_data_dict = self._group_by_coupler()
        if len(coupler_data_dict) == 0:
            logger.error("Dataset does not have valid coordinates")
        for this_coupler, coupler_data_vars in coupler_data_dict.items():
            ds = xr.merge([self.dataset[var] for var in coupler_data_vars])
            ds.attrs["coupler"] = this_coupler
            ds.attrs["node"] = self.name
            coupler_analysis_keywords = self.analysis_keywords.get(this_coupler, {})

            coupler_analysis = self.single_coupler_analysis_obj(
                self.name, self.redis_fields, **coupler_analysis_keywords
            )
            coupler_analysis.data_path = self.data_path
            qoi = coupler_analysis.process_coupler(ds, this_coupler)
            if hasattr(coupler_analysis, "processed_dataset"):
                processed_coupler_dataset = coupler_analysis.processed_dataset
                self.processed_dataset = xr.merge(
                    [self.processed_dataset, processed_coupler_dataset]
                )
            coupler_analysis.plotter(figures_dictionary=self.figures_dictionary)
            analysis_results[this_coupler] = qoi

        return analysis_results

    def _group_by_coupler(self):
        coupler_data_dict = collections.defaultdict(set)
        for var in self.dataset.data_vars:
            if hasattr(self.dataset[var], "element"):
                # couplers will have _ in their name
                if "_" in self.dataset[var].element:
                    this_coupler = self.dataset[var].element
                    coupler_data_dict[this_coupler].add(var)
        return coupler_data_dict
