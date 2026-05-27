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
from abc import ABC, abstractmethod
from typing import List

# TODO: we should have a conditional import depending on a feature flag here
import numpy as np
import xarray as xr

from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.lib.base.utils.analysis_utils import filter_ds_by_element
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
        self.figures = []

    @property
    def qoi(self) -> "QOI":
        return self._qoi

    @qoi.setter
    def qoi(self, value: "QOI"):
        self._qoi = value

    @abstractmethod
    def analyze_node(self, dataset: xr.Dataset) -> dict[str, QOI]:
        """
        Run the fitting of the analysis function

        Returns:
            The quantity of interest as QOI wrapped object

        """

    def _manage_plots(self, column_grid: int, plots_per_qubit: int):
        n_vars = len(self.data_vars)
        nrows = int(np.ceil(n_vars / column_grid)) * plots_per_qubit
        ncols = min(column_grid, n_vars)

        fig, axs = create_figure_with_top_band(nrows, ncols)
        return fig, axs


class BaseAllQubitsAnalysis(BaseNodeAnalysis, ABC):
    """
    Base class for the analysis of all qubits in a node
    """

    single_qubit_analysis_obj: "BaseQubitAnalysis"

    def __init__(self, name: str, redis_fields):
        super().__init__()
        self.name = name
        self.redis_fields = redis_fields
        self.dataset = xr.Dataset()
        self.data_vars = None
        self.coords = None

        self.qubit_analyses: List[BaseQubitAnalysis] = []

        self.column_grid = 5
        self.plots_per_qubit = 1

    def analyze_node(self, dataset: xr.Dataset) -> dict[str, QOI]:
        """
        Analyze the node and save the results to redis.
        Args:
            dataset: the full configured result dataset

        Returns:
            analysis_results: Dictionary with the analysis results for each qubit
        """

        self.dataset = dataset
        self.coords = self.dataset.coords
        self.data_vars = self.dataset.data_vars
        self.fig, self.axs = self._manage_plots(self.column_grid, self.plots_per_qubit)
        analysis_results = self._analyze_all_qubits()
        self._fill_plots()
        self.figures = [self.fig]
        return analysis_results

    def _analyze_all_qubits(self):
        analysis_results = {}
        qubits = self.dataset.elements
        if isinstance(qubits, list):
            qubits.sort(
                key=lambda x: int(x[1:])
            )  # TODO: move this to configure_dataset
        for this_qubit in qubits:
            # TODO: this object is created for every single qubit
            qubit_analysis: BaseQubitAnalysis = self.single_qubit_analysis_obj(
                self.name, self.redis_fields
            )

            partial_ds = filter_ds_by_element(self.dataset, this_qubit)
            analysis_results[this_qubit] = qubit_analysis.process_qubit(partial_ds)
            self.qubit_analyses.append(qubit_analysis)

        return analysis_results

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

    def process_qubit(self, dataset) -> "QOI":
        """
        Setup the qubit data and analyze it.
        Args:
            dataset: xarray dataset with the qubit data
            qubit_element: name of the qubit element
        Returns:
            QOI: Quantity of interest as QOI wrapped object
        """

        self.dataset = dataset
        self.qubit = dataset.qubit
        self._set_data_variables()
        self._compute_magnitudes()
        self._qoi = self.analyse_qubit()
        return self._qoi

    def _set_data_variables(self):
        self.coord = self.dataset.coords  # TODO: is this used anywhere?
        # TODO: how is this used?
        self.data_var = list(self.dataset.data_vars.keys())[0]

    def _compute_magnitudes(self):
        self.S21 = self.dataset
        self.magnitudes = xr.ufuncs.abs(self.S21)

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
    def analyse_qubit(self) -> "QOI":
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

    def process_coupler(self, dataset: xr.Dataset, coupler_element) -> "QOI":
        self.control_qubit, self.target_qubit = (
            CONFIG.device.get_control_target_qubit_pair_by_coupler(coupler_element)
        )
        self.dataset = dataset
        self.coupler = coupler_element
        self.coord = dataset.coords
        self.data_var = list(dataset.data_vars.keys())[0]

        self.S21 = dataset
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
                raise ValueError("No control or target qubits")

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

    def analyze_node(self, dataset: xr.Dataset) -> dict[str, QOI]:
        """
        Analyze the node and save the results to redis.
        Args:
            dataset: the full configured result dataset

        Returns:
            analysis_results: Dictionary with the analysis results for each qubit
        """

        self.dataset = dataset
        self.coords = self.dataset.coords
        self.data_vars = self.dataset.data_vars
        analysis_results = self._analyze_all_couplers()
        self.adjust_figures()
        return analysis_results

    def adjust_figures(self):
        """
        modify the figures dictionary attributed of the current analysis
        so the figures have a more standardized appearance
        """
        # if the dictionary is empty do nothing
        if not self.figures_dictionary:
            return

        self.figures = []
        for coupler, figure_list in self.figures_dictionary.items():
            for fig in figure_list:
                # this corresponds to faceted plots
                if fig.axes[0].get_gridspec().get_geometry() == (2, 3):
                    fig.set_size_inches(14, 9)
                else:
                    nrows = fig.axes[0].get_gridspec().nrows
                    ncols = fig.axes[0].get_gridspec().ncols
                    if nrows == 1 and ncols == 1:
                        fig.set_size_inches(9, 6)
                    elif nrows == 1 and ncols == 2:
                        fig.set_size_inches(12, 8)
                    else:
                        fig.set_size_inches(ncols * 6, nrows * 4)

                # some slack for the figure x and y labels
                fig.tight_layout(rect=[0.05, 0.05, 1, 0.98])
                # fig.savefig(preview_path, bbox_inches="tight", dpi=100)
            self.figures += figure_list

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
