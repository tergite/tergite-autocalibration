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
import xarray as xr

# TODO: we should have a conditional import depending on a feature flag here
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

import numpy as np

from tergite_autocalibration.config.settings import REDIS_CONNECTION
from tergite_autocalibration.tools.mss.convert import structured_redis_storage
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
    def analyse_qubit(self) -> "QOI":
        """
        Run the fitting of the analysis function

        Returns:
            The quantity of interest as QOI wrapped object

        """
        pass

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
    def update_redis_trusted_values(
        self, node: str, this_element: str
    ):
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

    def manage_plots(self, column_grid: int, plots_per_qubit: int):
        n_vars = len(self.data_vars)
        n_coords = len(self.coords)
        print("nvars: ", n_vars)
        print("n_coords: ", n_coords)

        rows = int(np.ceil(n_vars / column_grid))
        rows = rows * plots_per_qubit

        fig, axs = plt.subplots(
            nrows=rows,
            ncols=np.min((n_vars, n_coords, column_grid)),
            squeeze=False,
            figsize=(column_grid * 5, rows * 5),
        )

        return fig, axs

    def save_plots(self, data_path: Path):
        self.fig.tight_layout()
        preview_path = data_path / f"{self.name}_preview.png"
        full_path = data_path / f"{self.name}.png"
        self.fig.savefig(preview_path, bbox_inches="tight", dpi=100)
        self.fig.savefig(full_path, bbox_inches="tight", dpi=400)
        plt.show(block=False)
        plt.pause(5)
        plt.close()
        print(f"Plots saved to {preview_path} and {full_path}")

class BaseAllQubitsAnalysis(BaseNodeAnalysis, ABC):
    single_qubit_analysis_obj: "BaseQubitAnalysis"

    def __init__(self, name, redis_fields):
        print("here")
        self.name = name
        self.redis_fields = redis_fields
        self.dataset = None
        self.data_vars = None
        self.coords = None

        self.qubit_analyses = []
  
        self.column_grid=5
        self.plots_per_qubit=1

    def analyze_node(self, data_path: Path):
        self.dataset = self.open_dataset(data_path)
        self.coords = self.dataset.coords
        self.data_vars = self.dataset.data_vars
        self.fig, self.axs = self.manage_plots(self.column_grid, self.plots_per_qubit)
        analysis_results = self._analyze_all_qubits()
        self._fill_plots()
        self.save_plots(data_path)
        return analysis_results

    def open_dataset(self, data_path: Path):
        dataset_path = data_path / "dataset_0.hdf5" 
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

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
                ds = ds.sel({selected_coord_name: slice(None)})  # Select all data along this coordinate

                qubit_analysis = self.single_qubit_analysis_obj(self.name, self.redis_fields)
                qubit_analysis._analyze_qubit(ds, this_qubit)
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
        self.dataset = None
        self.S21 = None
        self.data_var = None
        self.qubit = None
        self.coord = None

    def _analyze_qubit(self, dataset, qubit_element):
        self.dataset = dataset
        self.qubit = dataset.attrs["qubit"]
        self.coord = dataset.coords
        self.data_var = list(dataset.data_vars.keys())[0]  # Assume the first data_var is relevant
        self.S21 = dataset.isel(ReIm=0) + 1j * dataset.isel(ReIm=1)
        self.magnitudes = np.abs(self.S21)
        self._qoi = self.analyse_qubit()

        self.update_redis_trusted_values(self.name, qubit_element)
        return {qubit_element: dict(zip(self.redis_fields, self._qoi))}      

    def _plot(self, primary_axis):
        self.plotter(primary_axis)  # Assuming node_analysis object is available

        # Customize plot as needed
        handles, labels = primary_axis.get_legend_handles_labels()
        patch = mpatches.Patch(color="red", label=f"{self.qubit}")
        handles.append(patch)
        primary_axis.legend(handles=handles, fontsize="small")

class BaseCouplerAnalysis(BaseAnalysis, ABC):

    def run_analysis(self, data_path: Path):
        self.dataset = self.open_datasets(data_path)
        this_element = self._extract_coupler_info()
        analysis_results = self._run_coupler_analysis(this_element)

        return analysis_results

    @abstractmethod
    def open_datasets(data_path, number_of_files):
        pass


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
        self._qoi = self.analyse_qubit()
        self.update_redis_trusted_values(self.name, this_element)
        return {this_element: dict(zip(self.redis_field, self._qoi))}
