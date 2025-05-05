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

# TODO: we should have a conditional import depending on a feature flag here
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.tools.mss.convert import structured_redis_storage
from tergite_autocalibration.utils.dto.qoi import QOI
from tergite_autocalibration.utils.logging import logger


class BaseAnalysis(ABC):
    """
    Base class for the analysis
    """

    def __init__(self):
        self._qoi = None
        self.redis_fields = ""

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
        pass

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
        self._qoi = None
        self.redis_fields = ""

    @property
    def qoi(self) -> "QOI":
        return self._qoi

    @qoi.setter
    def qoi(self, value: "QOI"):
        self._qoi = value

    @abstractmethod
    def analyze_node(self) -> "QOI":
        """
        Run the fitting of the analysis function

        Returns:
            The quantity of interest as QOI wrapped object

        """
        pass

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

    def manage_plots(self, column_grid: int, plots_per_qubit: int):
        n_vars = len(self.data_vars)
        n_coords = len(self.coords)

        rows = int(np.ceil(n_vars / column_grid))
        rows = rows * plots_per_qubit

        fig, axs = plt.subplots(
            nrows=rows,
            ncols=np.min((n_vars, n_coords, column_grid)),
            squeeze=False,
            figsize=(column_grid * 5, rows * 5),
        )

        return fig, axs

    def save_plots(self):
        self.fig.tight_layout()
        preview_path = self.data_path / f"{self.name}_preview.png"
        full_path = self.data_path / f"{self.name}.png"
        logger.info("Saving Plots")
        self.fig.savefig(preview_path, bbox_inches="tight", dpi=100)
        self.fig.savefig(full_path, bbox_inches="tight", dpi=400)
        plt.show(block=True)
        logger.info(f"Plots saved to {preview_path} and {full_path}")
        plt.close()


class BaseAllQubitsAnalysis(BaseNodeAnalysis, ABC):
    single_qubit_analysis_obj: "BaseQubitAnalysis"

    def __init__(self, name: str, redis_fields):
        self.name = name
        self.redis_fields = redis_fields
        self.dataset = None
        self.data_vars = None
        self.coords = None

        self.qubit_analyses = []

        self.column_grid = 5
        self.plots_per_qubit = 1

    def analyze_node(self, data_path: Path, index: int = 0):
        self.data_path = Path(data_path)
        self.dataset = self.open_dataset(index=index)
        self.coords = self.dataset.coords
        self.data_vars = self.dataset.data_vars
        self.fig, self.axs = self.manage_plots(self.column_grid, self.plots_per_qubit)
        analysis_results = self._analyze_all_qubits()
        self._fill_plots()
        self.save_plots()
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

                qubit_analysis = self.single_qubit_analysis_obj(
                    self.name, self.redis_fields
                )
                # NOTE: coord initialization cannot be done in the __init__ because
                # the dataset is loaded by the process_qubit method.
                # in other words the __init__ of the analysis class is not aware of the
                # dataset to be analyzed
                analysis_results[this_qubit] = qubit_analysis.process_qubit(
                    ds, this_qubit
                )  # this_qubit should be qXX
                # analysis_results[this_qubit] = dict(zip(self.redis_fields, result))
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
            analysis._plot(primary_axis)


class BaseQubitAnalysis(BaseAnalysis, ABC):
    def __init__(self, name, redis_fields):
        self.name = name
        self.redis_fields = redis_fields
        self.dataset: xr.Dataset
        self.S21: xr.DataArray
        self.data_var = None
        self.qubit: str
        self.coord = None

    def process_qubit(self, dataset, qubit_element):
        self.dataset = dataset
        self.qubit = qubit_element
        self.coord = dataset.coords  # What is this doing?
        self.data_var = list(dataset.data_vars.keys())[
            0
        ]  # Assume the first data_var is relevant
        self.S21 = dataset.isel(ReIm=0) + 1j * dataset.isel(ReIm=1)
        self.magnitudes = np.abs(self.S21)
        self._qoi = self.analyse_qubit()

        return self._qoi

    def _plot(self, primary_axis):
        self.plotter(primary_axis)  # Assuming node_analysis object is available

        # Customize plot as needed
        handles, labels = primary_axis.get_legend_handles_labels()
        patch = mpatches.Patch(color="red", label=f"{self.qubit}")
        handles.append(patch)
        primary_axis.legend(handles=handles, fontsize="small")

    @abstractmethod
    def analyse_qubit(self) -> "QOI":
        """
        Run the fitting of the analysis function

        Returns:
            The quantity of interest as QOI wrapped object

        """
        pass


class BaseCouplerAnalysis(BaseAnalysis, ABC):
    def __init__(self, name, redis_fields):
        self.name = name
        self.redis_fields = redis_fields
        self.dataset = None
        self.data_vars = None
        self.coords = None
        self.name_qubit_1 = ""
        self.name_qubit_2 = ""

    def process_coupler(self, dataset, coupler_element):
        self.name_qubit_1 = coupler_element[0:3]
        self.name_qubit_2 = coupler_element[4:7]
        self.dataset = dataset
        self.coupler = coupler_element
        self.coord = dataset.coords
        self.data_var = list(dataset.data_vars.keys())[
            0
        ]  # Assume the first data_var is relevant
        self.S21 = dataset.isel(ReIm=0) + 1j * dataset.isel(ReIm=1)
        self.magnitudes = np.abs(self.S21)

        analysis_results = self._run_coupler_analysis(coupler_element)
        # TODO: This function does not have any effect as long as no coupler qois are passed
        # Note: As soon as anyone creates a merge request or has merge conflicts at
        #       this very position, we can determine a strategy on how coupler qois are passed
        # self.update_redis_trusted_values(self.name, coupler_element)

        return analysis_results

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

    def _run_coupler_analysis(self, this_element: str):
        self._qoi = self.analyze_coupler()
        return {this_element: dict(zip(self.redis_fields, self._qoi))}

    def _plot(self, primary_axis, secondary_axis):
        self.plotter(
            primary_axis, secondary_axis
        )  # Assuming node_analysis object is available

        # Customize plot as needed
        patch = mpatches.Patch(color="green", label=f"{self.coupler}")

        # handles, labels = primary_axis.get_legend_handles_labels()
        # handles.append(patch)
        # primary_axis.legend(handles=handles, fontsize="small")
        # handles, labels = secondary_axis.get_legend_handles_labels()
        # handles.append(patch)
        # secondary_axis.legend(handles=handles, fontsize="small")

    @abstractmethod
    def analyze_coupler(self):
        pass


class BaseAllCouplersAnalysis(BaseNodeAnalysis, ABC):
    single_coupler_analysis_obj: "BaseCouplerAnalysis"

    def __init__(self, name, redis_fields):
        self.name = name
        self.redis_fields = redis_fields
        self.dataset = None
        self.data_vars = None
        self.coords = None

        self.coupler_analyses = []

        self.column_grid = 2
        self.plots_per_qubit = 1

    def analyze_node(self, data_path: Path):
        self.data_path = Path(data_path)
        self.dataset = self.open_dataset()
        self.coords = self.dataset.coords
        self.data_vars = self.dataset.data_vars
        self.fig, self.axs = self.manage_plots(self.column_grid, self.plots_per_qubit)
        analysis_results = self._analyze_all_couplers()
        self._fill_plots()
        self.save_plots()
        return analysis_results

    def _analyze_all_couplers(self):
        analysis_results = {}
        coupler_data_dict = self._group_by_coupler()
        index = 0
        if len(coupler_data_dict) == 0:
            logger.error("Dataset does not have valid coordinates")
        logger.info(coupler_data_dict)
        for this_coupler, coupler_data_vars in coupler_data_dict.items():
            logger.info(this_coupler)
            ds = xr.merge([self.dataset[var] for var in coupler_data_vars])
            ds.attrs["coupler"] = this_coupler
            ds.attrs["node"] = self.name

            # matching_coords = [coord for coord in ds.coords if this_coupler in coord]
            coupler_analysis = self.single_coupler_analysis_obj(
                self.name, self.redis_fields
            )
            coupler_analysis.data_path = self.data_path
            coupler_analysis.process_coupler(ds, this_coupler)
            self.coupler_analyses.append(coupler_analysis)

            index = index + 1

        return analysis_results

    def _group_by_coupler(self):
        coupler_data_dict = collections.defaultdict(set)
        for var in self.dataset.data_vars:
            if "_" in self.dataset[var].element:
                this_coupler = self.dataset[var].element
                coupler_data_dict[this_coupler].add(var)

        return coupler_data_dict

    def _fill_plots(self):
        for index, analysis in enumerate(self.coupler_analyses):
            primary_plot_row = self.plots_per_qubit * (index // self.column_grid)
            primary_axis = self.axs[primary_plot_row, index % self.column_grid]
            secondary_axis = self.axs[primary_plot_row, (index + 1) % self.column_grid]
            analysis._plot(primary_axis, secondary_axis)
