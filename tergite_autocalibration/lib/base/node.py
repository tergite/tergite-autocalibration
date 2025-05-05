# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2024, 2025
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
from typing import Tuple

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
from quantify_scheduler.device_under_test.quantum_device import QuantumDevice

from tergite_autocalibration.config.globals import PLOTTING_BACKEND
from tergite_autocalibration.lib.utils.redis import update_redis_trusted_values
from tergite_autocalibration.utils.logging import logger
from tergite_autocalibration.lib.base.analysis import BaseNodeAnalysis
from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.lib.utils.device import DeviceConfiguration
from tergite_autocalibration.lib.utils.schedule_execution import execute_schedule
from tergite_autocalibration.utils.dto.enums import MeasurementMode
from tergite_autocalibration.utils.io.dataset import save_dataset

colorama_init()

matplotlib.use(PLOTTING_BACKEND)


class BaseNode(abc.ABC):
    measurement_obj: "BaseMeasurement"
    analysis_obj: "BaseNodeAnalysis"

    def __init__(self, name: str, **node_dictionary):
        self.name = name
        self.node_dictionary = node_dictionary
        self.lab_instr_coordinator: InstrumentCoordinator
        self._results = {}
        self.schedule_samplespace = {}
        self.external_samplespace = {}
        self.redis_fields = []
        self.all_qubits = []

        # These may be modified while the node runs
        self.outer_schedule_samplespace = {}
        self.initial_schedule_samplespace = {}
        self.reduced_external_samplespace = {}
        self.loops = None
        self.schedule_keywords = {}

        self.samplespace = self.schedule_samplespace | self.external_samplespace

        self.device_manager: DeviceConfiguration = None
        self.device: QuantumDevice = None

    def measure_node(self, cluster_status) -> xarray.Dataset:
        result_dataset = xarray.Dataset()
        """
        To be implemented by the Classes that define the Node Type:
        ScheduleNode or ExternalParameterNode
        """
        return result_dataset

    def precompile(self, schedule_samplespace: dict) -> CompiledSchedule:
        schedule: CompiledSchedule = None
        """
        To be implemented by the Classes that define the Node Type:
        ScheduleNode or ExternalParameterNode
        """
        return schedule

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
        logger.status(
            f"schedule_duration = {Fore.CYAN}{Style.BRIGHT}{message}{Style.RESET_ALL}"
        )

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

        raw_dataset = execute_schedule(
            compiled_schedule,
            schedule_duration,
            self.lab_instr_coordinator,
            cluster_status,
        )
        result_dataset = self.configure_dataset(raw_dataset)

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

    def calibrate(self, data_path: Path, cluster_status):
        if cluster_status != MeasurementMode.re_analyse:
            pass
            result_dataset = self.measure_node(cluster_status)
            self.device_manager.save_serial_device(self.name, self.device, data_path)
            # After the measurement free the device resources
            save_dataset(result_dataset, self.name, data_path)
        self.device_manager.close_device()
        self.post_process(data_path)
        logger.info("analysis completed")

    def post_process(self, data_path: Path):
        analysis_kwargs = getattr(self, "analysis_kwargs", dict())
        node_analysis = self.analysis_obj(
            self.name, self.redis_fields, **analysis_kwargs
        )
        self._results = node_analysis.analyze_node(data_path)
        for element_id_, qois_ in self._results.items():
            update_redis_trusted_values(self.name, element_id_, qoi=qois_)
        return self._results

    def configure_dataset(
        self,
        raw_ds: xarray.Dataset,
    ) -> xarray.Dataset:
        """
        The dataset retrieved from the instrument coordinator is
        too bare-bones. Here the dims, coords and data_vars are configured
        """
        dataset = xarray.Dataset(attrs={"elements": []})

        raw_ds_keys = raw_ds.data_vars.keys()
        measurement_qubits = self.all_qubits
        samplespace = self.schedule_samplespace

        sweep_quantities = samplespace.keys()

        n_qubits = len(measurement_qubits)

        for key in raw_ds_keys:
            key_indx = key % n_qubits  # this is to handle ro_opt_frequencies node where
            coords_dict = {}
            measured_qubit = measurement_qubits[key_indx]
            dimensions = self.dimensions

            # TODO: this is flagged for removal.
            if "ssro" in self.name and self.name != "randomized_benchmarking_ssro":
                shots = int(len(raw_ds[key].values[0]) / (np.prod(dimensions)))
                coords_dict["shot"] = (
                    "shot",
                    range(shots),
                    {"qubit": measured_qubit, "long_name": "shot", "units": "NA"},
                )

            for quantity in sweep_quantities:
                # eg settable_elements -> ['q1','q2',...] or ['q1_q2','q3_q4',...] :
                settable_elements = samplespace[quantity].keys()

                # distinguish if the settable is on a qubit or a coupler:
                if measured_qubit in settable_elements:
                    element = measured_qubit
                    element_type = "qubit"
                else:
                    matching = [s for s in settable_elements if measured_qubit in s]
                    # TODO: len(matching) == 1 implies that we operate on only 1 coupler.
                    # To be changed in future
                    if len(matching) == 1 and "_" in matching[0]:
                        element = matching[0]
                        element_type = "coupler"
                    else:
                        raise (ValueError)

                coord_key = quantity + element

                settable_values = samplespace[quantity][element]
                coord_attrs = {
                    "element_type": element_type,  # 'element_type' is ether 'qubit' or 'coupler'
                    element_type: element,
                    "measured_qubit": measured_qubit,
                    "long_name": f"{coord_key}",
                    "units": "NA",
                }

                if not isinstance(settable_values, Iterable):
                    settable_values = np.array([settable_values])

                coords_dict[coord_key] = (coord_key, settable_values, coord_attrs)

            if self.loops is not None:
                coords_dict["loops"] = (
                    "loops",
                    np.arange(self.loops),
                    {"element_type": "NA"},
                )

            partial_ds = xarray.Dataset(coords=coords_dict)

            data_values = raw_ds[key].values

            # TODO: flagged for removal
            if "ssro" in self.name and self.name != "randomized_benchmarking_ssro":
                reshaping = np.array([shots])
                reshaping = np.append(reshaping, dimensions)
                data_values = data_values.reshape(*reshaping)
            elif "cz_parametrization" in self.name:
                reshaping = reversed(self.dimensions)
                data_values = data_values.reshape(*reshaping)
                data_values = np.transpose(data_values)
            else:
                data_values = data_values.reshape(*self.dimensions, order="F")

            # determine if this dataarray examines a qubit or a coupler:
            # TODO: this needs improvement
            element = measured_qubit
            if issubclass(self.__class__, CouplerNode):
                for coupler in self.couplers:
                    if element in coupler:
                        element = coupler
                        break

            attributes = {
                "qubit": measured_qubit,
                "element": element,
                "long_name": f"y{measured_qubit}",
                "units": "NA",
            }
            partial_ds[f"y{measured_qubit}"] = (
                tuple(coords_dict.keys()),
                data_values,
                attributes,
            )

            dataset = xarray.merge([dataset, partial_ds])
            dataset.attrs["elements"].append(element)

        return dataset


class QubitNode(BaseNode, abc.ABC):
    qubit_qois: list[str] | None = None

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name)
        self.all_qubits = all_qubits
        self.qubit_state = 0  # can be 0 or 1 or 2
        self.plots_per_qubit = 1  # can be 0 or 1 or 2

        if self.qubit_qois is not None:
            self.redis_fields = self.qubit_qois

        # NOTE: In the future this will be problematic.
        # Having the device creation in the init will prohibit concurrent
        # initialization of two different nodes
        self.device_manager = DeviceConfiguration(self.all_qubits, None)
        self.device = self.device_manager.configure_device(self.name)

    def precompile(self, schedule_samplespace: dict) -> CompiledSchedule:
        constants.GRID_TIME_TOLERANCE_TIME = 5e-2

        # TODO: put 'tof' out of its misery
        if self.name == "tof":
            return None, 1

        transmons = self.device_manager.transmons

        measurement_class = self.measurement_obj(transmons)
        schedule = measurement_class.schedule_function(
            **schedule_samplespace, **self.schedule_keywords
        )

        # TODO: Probably the compiler desn't need to be created every time self.precompile() is called.
        compiler = SerialCompiler(name=f"{self.name}_compiler")

        compilation_config = self.device.generate_compilation_config()
        logger.info("Starting Compiling")
        compiled_schedule = compiler.compile(
            schedule=schedule, config=compilation_config
        )

        return compiled_schedule

    def __str__(self):
        return f"Node representation for {self.name} on qubits {self.all_qubits}"

    def __format__(self, message):
        return f"Node representation for {self.name} on qubits {self.all_qubits}"

    def __repr__(self):
        return f"Node({self.name}, {self.all_qubits})"


class CouplerNode(BaseNode, abc.ABC):
    coupler_qois: list[str]

    def __init__(self, name: str, couplers: list[str], **node_dictionary):
        super().__init__(name)
        self.couplers = couplers
        self.edges = couplers
        self.all_qubits = self.get_coupled_qubits()
        self.plots_per_qubit = 1  # can be 0 or 1 or 2

        if self.coupler_qois is not None:
            self.redis_fields = self.coupler_qois

        # NOTE: In the future this will be problematic.
        # Having the device creation in the init will prohibit concurrent
        # initialization of two different nodes

        self.device_manager = DeviceConfiguration(self.all_qubits, self.couplers)
        self.device = self.device_manager.configure_device(self.name)

        self.validate()

    def get_coupled_qubits(self) -> list:
        coupled_qubits = []
        for coupler in self.couplers:
            qubits = coupler.split(sep="_")
            coupled_qubits.append(qubits[0])
            coupled_qubits.append(qubits[1])
        return coupled_qubits

    def validate(self) -> None:
        all_coupled_qubits = []
        for coupler in self.couplers:
            all_coupled_qubits += coupler.split("_")
        if len(all_coupled_qubits) > len(set(all_coupled_qubits)):
            logger.info("Couplers share qubits")
            raise ValueError("Improper Couplers")

    def precompile(self, schedule_samplespace: dict) -> CompiledSchedule:
        constants.GRID_TIME_TOLERANCE_TIME = 5e-2

        # TODO: put 'tof' out of its misery
        if self.name == "tof":
            return None, 1

        transmons = self.device_manager.transmons
        edges = self.device_manager.edges
        measurement_class = self.measurement_obj(transmons, edges)
        schedule = measurement_class.schedule_function(
            **schedule_samplespace, **self.schedule_keywords
        )

        # TODO: Probably the compiler desn't need to be created every time self.precompile() is called.
        compiler = SerialCompiler(name=f"{self.name}_compiler")

        compilation_config = self.device.generate_compilation_config()
        logger.info("Starting Compiling")
        compiled_schedule = compiler.compile(
            schedule=schedule, config=compilation_config
        )

        return compiled_schedule
