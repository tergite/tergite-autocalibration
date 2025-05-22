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

# TODO: we should have a conditional import depending on a feature flag here
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from tergite_autocalibration.lib.base.utils.figure_utils import (
    create_figure_with_top_band,
)
from tergite_autocalibration.lib.utils.redis import update_redis_trusted_values
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
    def plotter(self, ax: "plt.Axes"):
        """
        Plot the fitted values from the analysis

        Args:
            ax: The axis object from matplotlib to be plotted

        Returns:
            None, will just plot the fitted values

        """

    def rotate_to_probability_axis(self, complex_measurement_data):
        # TODO: THIS DOESNT BELONG HERE
        """
        Rotates the S21 IQ points to the real - normalized axis
        that describes the |0> - |1> axis.
        !!! It Assumes that complex_measurement_data[-2] corresponds to the |0>
                        and complex_measurement_data[-1] corresponds to the |1>
        """
        measurements = complex_measurement_data.flatten()
        data = measurements[:-2]
        calibration_0 = measurements[-2]
        calibration_1 = measurements[-1]
        displacement_vector = calibration_1 - calibration_0
        data_translated_to_zero = data - calibration_0

        rotation_angle = np.angle(displacement_vector)
        rotated_data = data_translated_to_zero * np.exp(-1j * rotation_angle)
        rotated_0 = calibration_0 * np.exp(-1j * rotation_angle)
        rotated_1 = calibration_1 * np.exp(-1j * rotation_angle)
        normalization = (rotated_1 - rotated_0).real
        real_rotated_data = rotated_data.real
        normalized_data = real_rotated_data / normalization
        return normalized_data


class BaseNodeAnalysis(ABC):
    """
    Base class for the analysis
    """

    def __init__(self):
        self.name = ""
        self._qoi = None
        self.redis_fields = ""
        self.data_path = ""
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
    def analyze_node(self, data_path: Path, index: int = 0) -> QOI:
        """
        Run the fitting of the analysis function

        Returns:
            The quantity of interest as QOI wrapped object

        """

    def open_dataset(self, index: int = 0) -> xr.Dataset:
        """
        Open the dataset for the analysis.

        Args:
            index: By default 0 for most of the measurements, can be set to load multiple datasets.

        Returns:
            xarray.Dataset with measurement results

        """
        dataset_name = f"dataset_{self.name}_{index}.hdf5"
        dataset_path = os.path.join(self.data_path, dataset_name)
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

        logger.info("Open dataset " + str(dataset_path))
        return xr.open_dataset(dataset_path)

    def _manage_plots(self, column_grid: int, plots_per_qubit: int):
        n_vars = len(self.data_vars)
        rows = int(np.ceil(n_vars / column_grid)) * plots_per_qubit

        fig, axs = create_figure_with_top_band(rows, column_grid)

        return fig, axs

    def _save_plots(self):
        preview_path = self.data_path / f"{self.name}_preview.png"
        full_path = self.data_path / f"{self.name}.png"
        logger.info("Saving Plots")
        self.fig.savefig(preview_path, bbox_inches="tight", dpi=100)
        self.fig.savefig(full_path, bbox_inches="tight", dpi=400)
        plt.show(block=True)
        logger.info(f"Plots saved to {preview_path} and {full_path}")
        plt.close()

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

    def analyze_node(self, data_path: Path, index: int = 0) -> QOI:
        """
        Analyze the node and save the results to redis.
        Args:
            data_path: Path to the dataset
            index: Index of the dataset to be analyzed

        Returns:
            analysis_results: Dictionary with the analysis results for each qubit
        """

        self.data_path = Path(data_path)
        self.dataset = self.open_dataset(index=index)
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
        index = 0
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

            index = index + 1

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

    def __init__(self, name, redis_fields):
        super().__init__()
        self.name = name
        self.redis_fields = redis_fields
        self.dataset = None
        self.data_vars = None
        self.coords = None
        self.coupler = ""
        self.name_qubit_1 = ""
        self.name_qubit_2 = ""

    def process_coupler(self, dataset, coupler_element) -> QOI:
        """
        Setup the coupler data and analyze it.
        Args:
            dataset: xarray dataset with the coupler data
            coupler_element: name of the coupler element
        Returns:
            QOI: Quantity of interest as QOI wrapped object
        """

        self.dataset = dataset
        self.coupler = coupler_element
        self._extract_qubit_names()
        self._set_data_variables()
        self._compute_magnitudes()
        self._qoi = self.analyze_coupler()
        return self._qoi

    def _extract_qubit_names(self):
        self.name_qubit_1 = self.coupler[0:3]
        self.name_qubit_2 = self.coupler[4:7]

    def _set_data_variables(self):
        self.coord = self.dataset.coords
        self.data_var = list(self.dataset.data_vars.keys())[0]

    def _compute_magnitudes(self):
        self.S21 = self.dataset.isel(ReIm=0) + 1j * self.dataset.isel(ReIm=1)
        self.magnitudes = np.abs(self.S21)

    def _extract_coupler_info(self):
        for settable in self.dataset.coords:
            try:
                if self.dataset[settable].attrs["element_type"] == "coupler":
                    element_type = "coupler"
                    this_element = self.dataset[settable].attrs[element_type]
                    return this_element
            except KeyError:
                logger.info(f"No element_type for {settable}")
        return None

    @abstractmethod
    def plotter(self, primary_axis, secondary_axis):
        """
        Plot the fitted values from the analysis
        Args:
            primary_axis: The axis object from matplotlib to be plotted
            secondary_axis: The axis object from matplotlib to be plotted
        Returns:
            None, will just plot the fitted values
        """

    def plot(self, primary_axis, secondary_axis):
        """
        Plot the fitted values from the analysis
        Args:
            primary_axis: The axis object from matplotlib to be plotted
            secondary_axis: The axis object from matplotlib to be plotted
        Returns:
            None, will just plot the fitted values
        """

        self.plotter(
            primary_axis, secondary_axis
        )  # Assuming node_analysis object is available

    @abstractmethod
    def analyze_coupler(self) -> QOI:
        """
        Run the actual analysis function
        Returns:
            The quantity of interest as QOI wrapped object
        """


class BaseAllCouplersAnalysis(BaseNodeAnalysis, ABC):
    """
    Base class for the analysis of all couplers in a node
    """

    single_coupler_analysis_obj: "BaseCouplerAnalysis"

    def __init__(self, name, redis_fields):
        super().__init__()
        self.name = name
        self.redis_fields = redis_fields
        self.dataset = None
        self.data_vars = None
        self.coords = None

        self.coupler_analyses: List[BaseCouplerAnalysis] = []

        self.column_grid = 4
        self.plots_per_qubit = 1
        self.plots_per_coupler = 2

    def analyze_node(self, data_path: Path, index: int = 0) -> QOI:
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
        self.fig, self.axs = self._manage_plots(self.column_grid, self.plots_per_qubit)
        analysis_results = self._analyze_all_couplers()
        self._fill_plots()
        self._save_plots()
        self._save_other_plots()
        return analysis_results

    def _analyze_all_couplers(self):
        analysis_results = {}
        coupler_data_dict = self._group_by_coupler()
        index = 0
        if len(coupler_data_dict) == 0:
            logger.error("Dataset does not have valid coordinates")
        for this_coupler, coupler_data_vars in coupler_data_dict.items():
            ds = xr.merge([self.dataset[var] for var in coupler_data_vars])
            ds.attrs["coupler"] = this_coupler
            ds.attrs["node"] = self.name

            # matching_coords = [coord for coord in ds.coords if this_coupler in coord]
            coupler_analysis: BaseCouplerAnalysis = self.single_coupler_analysis_obj(
                self.name, self.redis_fields
            )
            coupler_analysis.data_path = self.data_path
            result = coupler_analysis.process_coupler(ds, this_coupler)
            analysis_results[this_coupler] = result

            self.coupler_analyses.append(coupler_analysis)

            index = index + 1

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

    def _fill_plots(self):
        for index, analysis in enumerate(self.coupler_analyses):
            primary_plot_row = self.plots_per_qubit * (
                (index * self.plots_per_coupler) // self.column_grid
            )
            primary_axis = self.axs[
                primary_plot_row, (index * self.plots_per_coupler) % self.column_grid
            ]
            secondary_axis = self.axs[
                primary_plot_row,
                ((index * self.plots_per_coupler) + 1) % self.column_grid,
            ]

            analysis.plot(primary_axis, secondary_axis)

            # Get positions of both axes (left and right in the pair)
            self.fig.canvas.draw()
            bbox1 = primary_axis.get_position()
            bbox2 = secondary_axis.get_position()

            # Center horizontally between both plots
            x_center = (bbox1.x0 + bbox2.x1) / 2

            # Align just above the top of the tallest one
            y_top = max(bbox1.y1, bbox2.y1) + 0.015  # Slight padding

            # Add clean, aligned label
            self.fig.text(
                x_center,
                y_top,
                f"Coupler: {analysis.coupler}",
                ha="center",
                va="bottom",
                color="black",
                fontsize=13,
                fontweight="bold",
                transform=self.fig.transFigure,
            )
