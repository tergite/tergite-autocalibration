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

import abc
from collections.abc import Iterable
from pathlib import Path
from typing import List, Literal, Optional, Tuple

import matplotlib
import numpy as np
import quantify_scheduler.backends.qblox.constants as constants
import xarray
from colorama import Fore, Style
from colorama import init as colorama_init
from quantify_scheduler.backends import SerialCompiler
from quantify_scheduler.instrument_coordinator.instrument_coordinator import (
    CompiledSchedule,
    InstrumentCoordinator,
)

from tergite_autocalibration.config import settings
from tergite_autocalibration.lib.base.analysis import BaseNodeAnalysis
from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.lib.utils.device import DeviceConfiguration
from tergite_autocalibration.lib.utils.schedule_execution import execute_schedule
from tergite_autocalibration.utils.dataset_utils import configure_dataset, save_dataset
from tergite_autocalibration.utils.dto.enums import MeasurementMode
from tergite_autocalibration.utils.logger.tac_logger import logger

colorama_init()


matplotlib.use(settings.PLOTTING_BACKEND)


class BaseNode(abc.ABC):
    measurement_obj: "BaseMeasurement"
    analysis_obj: "BaseNodeAnalysis"
    qubit_qois: list[str] | None = None
    coupler_qois: list[str] | None = None

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = node_dictionary
        self.backup = False
        self.is_ar = False
        self.qubit_state = 0  # can be 0 or 1 or 2
        self.plots_per_qubit = 1  # can be 0 or 1 or 2
        self.couplers: Optional[List[str] | None] = None
        self.lab_instr_coordinator: InstrumentCoordinator
        self.measured_elements: Literal["Single_Qubits", "Couplers"] = "Single_Qubits"

        self.schedule_samplespace = {}
        self.external_samplespace = {}

        # These may be modified while the node runs
        self.outer_schedule_samplespace = {}
        self.initial_schedule_samplespace = {}
        self.reduced_external_samplespace = {}
        self.loops = None
        self.schedule_keywords = {}

        self.samplespace = self.schedule_samplespace | self.external_samplespace

        if self.qubit_qois is not None:
            self.redis_fields = self.qubit_qois
            if self.coupler_qois is not None:
                self.redis_fields = self.qubit_qois + self.coupler_qois
        elif self.coupler_qois is not None:
            self.redis_fields = self.coupler_qois
        else:
            raise ValueError(
                "Quantities of Interest are missing from the node implementation"
            )

        # NOTE: In the future this will be problematic.
        # Having the device creation in the init will prohibit concurrent
        # initialization of two different nodes
        self.device_manager = DeviceConfiguration(self.all_qubits, self.couplers)
        self.device = self.device_manager.configure_device(self.name)

    def measure_node(self, cluster_status) -> xarray.Dataset:
        result_dataset = xarray.Dataset()
        """
        To be implemented by the Classes that define the Node Type:
        ScheduleNode or ExternalParameterNode
        """
        return result_dataset

    def generate_dummy_dataset(self) -> xarray.Dataset:
        result_dataset = xarray.Dataset()
        """
        To be implemented by the Node Implementation Classes.
        """
        return result_dataset

    def pre_measurement_operation(self):
        """
        To be implemented by the child measurement nodes
        """
        pass

    def initial_operation(self):
        """
        To be implemented by the child measurement nodes.
        This is called before the execution of each and every iteration
        of the samples of the external samplespace.
        See coupler_spectroscopy for examples.
        """
        pass

    def final_operation(self):
        """
        To be implemented by the child measurement nodes.
        This is called after ALL the iteration samples of the
        external samplespace have been executed.
        e.g. set back the dc_current to 0 in coupler_spectroscopy.
        See coupler_spectroscopy for examples.
        """
        pass

    @property
    def dimensions(self) -> list:
        """
        array of dimensions used for raw dataset reshaping
        """
        schedule_settable_quantities = self.schedule_samplespace.keys()

        # keeping the first element, ASSUMING that all settable elements
        # have the same dimensions on their samplespace

        first_settable = list(schedule_settable_quantities)[0]
        measured_elements = self.schedule_samplespace[first_settable].keys()
        first_element = list(measured_elements)[0]

        dimensions = []

        for quantity in schedule_settable_quantities:
            settable_values = self.schedule_samplespace[quantity][first_element]
            if not isinstance(settable_values, Iterable):
                settable_values = np.array([settable_values])
            dimensions.append(len(settable_values))

        if self.loops is not None:
            dimensions.append(self.loops)
        return dimensions

    def calibrate(self, data_path: Path, cluster_status):
        if cluster_status != MeasurementMode.re_analyse:
            result_dataset = self.measure_node(cluster_status)
            self.device_manager.save_serial_device(self.name, self.device, data_path)
            # After the measurement free the device resources
            save_dataset(result_dataset, self.name, data_path)
        self.device_manager.close_device()
        self.post_process(data_path)
        logger.info("analysis completed")

    def precompile(self, schedule_samplespace: dict) -> CompiledSchedule:
        constants.GRID_TIME_TOLERANCE_TIME = 5e-2

        # TODO: put 'tof' out of its misery
        if self.name == "tof":
            return None, 1

        transmons = self.device_manager.transmons

        if self.measured_elements == "Couplers":
            edges = self.device_manager.edges
            node_class = self.measurement_obj(transmons, edges)
        else:
            node_class = self.measurement_obj(transmons)
        schedule = node_class.schedule_function(
            **schedule_samplespace, **self.schedule_keywords
        )

        # TODO: Probably the compiler desn't need to be created every time self.precompile() is called.
        compiler = SerialCompiler(name=f"{self.name}_compiler")

        compilation_config = self.device.generate_compilation_config()
        logger.info("Starting Compiling")
        compiled_schedule = compiler.compile(
            schedule=schedule, config=compilation_config
        )

        # with open(f"timing_instructions_table_{self.name}.html", "w") as f:
        #     f.write(
        #         compiled_schedule.timing_table.hide(
        #             subset=["waveform_op_id", "operation_hash"], axis=1
        #         ).to_html()
        #     )

        # fig = compiled_schedule.plot_pulse_diagram(plot_backend="plotly")
        # fig.write_html(f"{self.name}_plotly.html")

        return compiled_schedule

    def measure_compiled_schedule(
        self,
        compiled_schedule: CompiledSchedule,
        cluster_status=MeasurementMode.real,
        measurement: Tuple[int, int] = (1, 1),
    ) -> xarray.Dataset:
        """
        Execute a measurement for a node and save the resulting dataset.

        Args:
            compiled_schedule (CompiledSchedule): The compiled schedule to execute.
            data_path (pathlib.Path): Path where the dataset will be saved.
            measurement (tuple): Tuple of (current_measurement, total_measurements).
        """

        schedule_duration = self._calculate_schedule_duration(compiled_schedule)
        self._print_measurement_info(schedule_duration, measurement)

        if cluster_status == MeasurementMode.real:
            raw_dataset = execute_schedule(
                compiled_schedule,
                schedule_duration,
                self.lab_instr_coordinator,
                cluster_status,
            )
        elif cluster_status == MeasurementMode.dummy:
            raw_dataset = self.generate_dummy_dataset()

        result_dataset = configure_dataset(raw_dataset, self)

        logger.info("Finished measurement")
        return result_dataset

    def _calculate_schedule_duration(
        self, compiled_schedule: CompiledSchedule
    ) -> float:
        """Calculate the total duration of the schedule."""
        duration = compiled_schedule.get_schedule_duration()
        if "loop_repetitions" in self.node_dictionary:
            duration *= self.node_dictionary["loop_repetitions"]
        return duration

    @staticmethod
    def _print_measurement_info(duration: float, measurement: Tuple[int, int]) -> None:
        """Print information about the current measurement."""
        measurement_message = (
            f". Measurement {measurement[0] + 1} of {measurement[1]}"
            if measurement[1] > 1
            else ""
        )
        # Format the message with duration and the measurement message
        message = f"{duration:.2f} sec{measurement_message}"
        print(
            f"schedule_duration = {Fore.CYAN}{Style.BRIGHT}{message}{Style.RESET_ALL}"
        )

    def post_process(self, data_path: Path):
        analysis_kwargs = getattr(self, "analysis_kwargs", dict())
        node_analysis = self.analysis_obj(
            self.name, self.redis_fields, **analysis_kwargs
        )
        analysis_results = node_analysis.analyze_node(data_path)
        return analysis_results

    def __str__(self):
        return f"Node representation for {self.name} on qubits {self.all_qubits}"

    def __format__(self, message):
        return f"Node representation for {self.name} on qubits {self.all_qubits}"

    def __repr__(self):
        return f"Node({self.name}, {self.all_qubits})"
