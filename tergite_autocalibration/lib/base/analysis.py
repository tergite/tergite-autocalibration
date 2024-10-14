# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
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
from pathlib import Path
import re
import pandas as pd
import xarray as xr

# TODO: we should have a conditional import depending on a feature flag here
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

import numpy as np

from tergite_autocalibration.config.settings import REDIS_CONNECTION
from tergite_autocalibration.tools.mss.convert import structured_redis_storage
from tergite_autocalibration.utils.logger.tac_logger import logger
from tergite_autocalibration.utils.dto.qoi import QOI


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

    # TODO: Alternative idea would be putting the redis handling into the QOI class
    # Pros: Would be completely high-level interfaced
    # Cons: We would have to define and implement several QOI classes
    # -> It is probably not that much effort to implement several QOI classes
    # -> We could start with a BaseQOI and add more as soon as needed
    def update_redis_trusted_values(self, node: str, this_element: str):
        for i, transmon_parameter in enumerate(self.redis_fields):
            if "_" in this_element:
                name = "couplers"
            else:
                name = "transmons"
            # Setting the value in the tergite-autocalibration-lite format
            REDIS_CONNECTION.hset(
                f"{name}:{this_element}", transmon_parameter, self._qoi[i]
            )
            # Setting the value in the standard redis storage
            structured_redis_storage(
                transmon_parameter, this_element.strip("q"), self._qoi[i]
            )
            REDIS_CONNECTION.hset(f"cs:{this_element}", node, "calibrated")

    def rotate_to_probability_axis(self, complex_measurement_data):
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

    @abstractmethod
    def open_dataset(self):
        pass

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
        self.fig.savefig(preview_path, bbox_inches="tight", dpi=100)
        self.fig.savefig(full_path, bbox_inches="tight", dpi=400)
        plt.show(block=False)
        plt.pause(5)
        plt.close()
        logger.info(f"Plots saved to {preview_path} and {full_path}")


class BaseAllQubitsAnalysis(BaseNodeAnalysis, ABC):
    single_qubit_analysis_obj: "BaseQubitAnalysis"

    def __init__(self, name, redis_fields):
        self.name = name
        self.redis_fields = redis_fields
        self.dataset = None
        self.data_vars = None
        self.coords = None

        self.qubit_analyses = []

        self.column_grid = 5
        self.plots_per_qubit = 1

    def analyze_node(self, data_path: Path):
        self.data_path = Path(data_path)
        self.dataset = self.open_dataset()
        self.coords = self.dataset.coords
        self.data_vars = self.dataset.data_vars
        self.fig, self.axs = self.manage_plots(self.column_grid, self.plots_per_qubit)
        analysis_results = self._analyze_all_qubits()
        self._fill_plots()
        self.save_plots()
        return analysis_results

    def open_dataset(self):
        dataset_path = self.data_path / "dataset_0.hdf5"
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

        logger.info("Open dataset " + str(dataset_path))
        return xr.open_dataset(dataset_path)

    def _analyze_all_qubits(self):
        analysis_results = {}
        qubit_data_dict = self._group_by_qubit()
        index = 0
        for this_qubit, qubit_data_vars in qubit_data_dict.items():
            ds = xr.merge([self.dataset[var] for var in qubit_data_vars])
            ds.attrs["qubit"] = this_qubit

            matching_coords = [coord for coord in ds.coords if this_qubit in coord]
            if matching_coords:
                selected_coord_name = matching_coords[0]
                ds = ds.sel(
                    {selected_coord_name: slice(None)}
                )  # Select all data along this coordinate

                qubit_analysis = self.single_qubit_analysis_obj(
                    self.name, self.redis_fields
                )
                qubit_analysis.process_qubit(
                    ds, this_qubit
                )  # this_qubit shoulq be qXX
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


class BaseAllQubitsRepeatAnalysis(BaseAllQubitsAnalysis, ABC):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.repeat_coordinate_name = ""

    def open_dataset(self):
        # Infer number of repeats by counting the number of dataset files
        data_files = sorted(self.data_path.glob("*.hdf5"))
        if not data_files:
            raise FileNotFoundError(f"No dataset files found in {self.data_path}")

        self.num_repeats = len(data_files)

        # Load the first dataset to infer the qubit names
        first_dataset = xr.open_dataset(data_files[0], engine="scipy")
        self.all_qubits = [
            var for var in first_dataset.data_vars if var.startswith("yq")
        ]

        datasets = []

        for qubit in self.all_qubits:
            qubit_datasets = []
            for repeat_idx, file_path in enumerate(data_files):
                file_path = self.data_path / f"dataset_{repeat_idx}.hdf5"

                ds = xr.open_dataset(file_path, engine="scipy")

                qubit_data = ds[[qubit]]

                repeat_coord = (
                    f"{self.repeat_coordinate_name}{qubit[1:]}"  # e.g., 'repeatq16'
                )
                if repeat_coord not in qubit_data.coords:
                    qubit_data = qubit_data.assign_coords({repeat_coord: repeat_idx})

                qubit_datasets.append(qubit_data)

            merged_qubit_data = xr.concat(qubit_datasets, dim=repeat_coord)
            datasets.append(merged_qubit_data)

        merged_datasets = xr.merge(datasets)

        return merged_datasets


class BaseQubitAnalysis(BaseAnalysis, ABC):
    def __init__(self, name, redis_fields):
        self.name = name
        self.redis_fields = redis_fields
        self.dataset = None
        self.S21 = None
        self.data_var = None
        self.qubit = None
        self.coord = None

    def process_qubit(self, dataset, qubit_element):
        self.dataset = dataset
        self.qubit = qubit_element
        self.coord = dataset.coords
        self.data_var = list(dataset.data_vars.keys())[
            0
        ]  # Assume the first data_var is relevant
        self.S21 = dataset.isel(ReIm=0) + 1j * dataset.isel(ReIm=1)
        self.magnitudes = np.abs(self.S21)
        self._qoi = self.analyse_qubit()

        self.update_redis_trusted_values(self.name, self.qubit)
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
        self.update_redis_trusted_values(self.name, coupler_element)

        return analysis_results

    def _extract_coupler_info(self):
        for settable in self.dataset.coords:
            try:
                if self.dataset[settable].attrs["element_type"] == "coupler":
                    element_type = "coupler"
                    this_element = self.dataset[settable].attrs[element_type]
                    return this_element
            except KeyError:
                print(f"No element_type for {settable}")
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
    def analyze_coupler():
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

    def open_dataset(self):
        dataset_path = self.data_path / "dataset_0.hdf5"
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

        logger.info("Open dataset " + str(dataset_path))
        return xr.open_dataset(dataset_path)

    def _analyze_all_couplers(self):
        analysis_results = {}
        coupler_data_dict = self._group_by_coupler()
        index = 0
        for this_coupler, coupler_data_vars in coupler_data_dict.items():
            ds = xr.merge([self.dataset[var] for var in coupler_data_vars])
            ds.attrs["coupler"] = this_coupler

            matching_coords = [coord for coord in ds.coords if this_coupler in coord]
            if matching_coords:
                selected_coord_name = matching_coords[0]
                ds = ds.sel(
                    {selected_coord_name: slice(None)}
                )  # Select all data along this coordinate

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
            # Find the relevant coordinate associated with the data variable
            for coord in self.dataset[var].coords:
                if "coupler" in self.dataset[coord].attrs:
                    # Extract the coupler name from the coordinate's attribute
                    this_coupler = self.dataset[coord].attrs["coupler"]
                    coupler_data_dict[this_coupler].add(var)
                    break  # Break if coupler found, move to the next variable

        return coupler_data_dict

    def _fill_plots(self):
        for index, analysis in enumerate(self.coupler_analyses):
            primary_plot_row = self.plots_per_qubit * (index // self.column_grid)
            primary_axis = self.axs[primary_plot_row, index % self.column_grid]
            secondary_axis = self.axs[primary_plot_row, (index + 1) % self.column_grid]
            analysis._plot(primary_axis, secondary_axis)


class BaseAllCouplersRepeatAnalysis(BaseAllCouplersAnalysis, ABC):
    single_coupler_analysis_obj: "BaseCouplerAnalysis"

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.repeat_coordinate_name = ""

    def _extract_coupler_from_coord(self, coord_name):
        """
        Extract the coupler name from a coordinate string.
        Assumes the coupler name is the last 7 characters of the coordinate, such as q06_q07.
        """
        match = re.search(r"q\d{2}_q\d{2}", coord_name)
        if match:
            return match.group(0)
        return None

    def _extract_coupler_from_coord(self, coord_name):
        # Assuming the coupler names follow a pattern like "q06_q07"
        match = re.search(r"q\d{2}_q\d{2}", coord_name)
        return match.group(0) if match else None

    def open_dataset(self):
        # Infer number of repeats by counting the number of dataset files
        data_files = sorted(self.data_path.glob("dataset_[0-9]*.hdf5"))
        if not data_files:
            raise FileNotFoundError(f"No dataset files found in {self.data_path}")

        self.num_repeats = len(data_files)

        # Load the first dataset to infer coupler-based coordinates
        first_dataset = xr.open_dataset(data_files[0], engine="scipy")

        # Step 1: Group data variables by qubit (assuming qubit data starts with 'yq')
        self.all_qubits = [
            var for var in first_dataset.data_vars if var.startswith("yq")
        ]

        # Step 2: Group coordinates by coupler (based on the pattern in the coordinate names)
        self.coupler_data_dict = collections.defaultdict(set)
        for coord in first_dataset.coords:
            coupler = self._extract_coupler_from_coord(coord)
            if coupler:
                self.coupler_data_dict[coupler].add(coord)

        print(f"Identified coupler data: {self.coupler_data_dict}")

        # You can now proceed to the rest of the merging process
        merged_dataset = self.open_and_merge_datasets(data_files)
        return merged_dataset

    def open_and_merge_datasets(self, data_files):
        merged_coupler_datasets = []

        for file_idx, file_path in enumerate(data_files):
            print(f"Opening dataset {file_idx + 1}/{len(data_files)}: {file_path}")
            ds = xr.open_dataset(file_path, engine="scipy")

            # Step 3: Extract qubit-related data and identify couplers
            for coupler, coords in self.coupler_data_dict.items():
                qubits = coupler.split("_")
                print(f"Processing coupler: {coupler}")

                qubit_data = [
                    ds[var]
                    for var in self.all_qubits
                    if any(f"q{qubit[-2:]}" in var for qubit in qubits)
                ]
                print(
                    f"Qubit data found for {coupler}: {[var.name for var in qubit_data]}"
                )

                if not qubit_data:
                    print(f"No qubit data found for {coupler}")
                    continue

                # Instead of merging, keep each qubit data separate
                for data in qubit_data:
                    data.name = f"{data.name}"  # Rename to avoid conflicts
                    merged_coupler_datasets.append(data)

        # Step 5: After all files are processed, merge everything into the final dataset
        if merged_coupler_datasets:
            print(
                f"Merging {len(merged_coupler_datasets)} datasets into final dataset."
            )
            final_merged_dataset = xr.merge(merged_coupler_datasets)
        else:
            final_merged_dataset = xr.Dataset()

        print(f"Final merged dataset variables: {list(final_merged_dataset.data_vars)}")

        return final_merged_dataset
