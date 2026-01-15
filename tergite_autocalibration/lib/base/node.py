# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2025
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

from collections.abc import Iterable
from pathlib import Path
from typing import Literal, Tuple

import matplotlib
import numpy as np
import quantify_scheduler.backends.qblox.constants as constants
import xarray
from colorama import Fore, Style
from colorama import init as colorama_init
from quantify_scheduler.backends import SerialCompiler
from quantify_scheduler.device_under_test.quantum_device import QuantumDevice
from quantify_scheduler.instrument_coordinator.instrument_coordinator import (
    CompiledSchedule,
    InstrumentCoordinator,
)

from tergite_autocalibration.config.globals import PLOTTING_BACKEND, REDIS_CONNECTION
from tergite_autocalibration.config.legacy import dh
from tergite_autocalibration.lib.base.analysis import BaseNodeAnalysis
from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.lib.base.node_interface import (
    MeasurementType,
    NodeInterface,
)
from tergite_autocalibration.lib.utils.device import (
    close_device_resources,
    configure_device,
    save_serial_device,
)
from tergite_autocalibration.lib.utils.redis import update_redis_trusted_values
from tergite_autocalibration.lib.utils.schedule_execution import execute_schedule
from tergite_autocalibration.utils.dto.enums import MeasurementMode
from tergite_autocalibration.utils.hardware.spi import SpiDAC
from tergite_autocalibration.utils.io.dataset import save_dataset
from tergite_autocalibration.utils.logging import logger
from tergite_autocalibration.utils.measurement_utils import samplespace_dimensions

colorama_init()

matplotlib.use(PLOTTING_BACKEND)


class BaseNode(NodeInterface):
    measurement_obj: "BaseMeasurement"
    analysis_obj: "BaseNodeAnalysis"
    measurement_type: "MeasurementType"

    def __init__(self, name: str, **node_dictionary):
        self.name = name
        self.node_dictionary = node_dictionary
        self.lab_instr_coordinator: InstrumentCoordinator
        self.spi_manager: SpiDAC
        self.schedule_samplespace = {}
        self.external_samplespace = {}
        self.redis_fields = []
        self.all_qubits = []

        # These may be modified while the node runs
        self.outer_schedule_samplespace = {}
        self.reduced_external_samplespace = {}
        self.loops = None
        self.schedule_keywords = {}
        self.analysis_keywords = {}

        self.samplespace = self.schedule_samplespace | self.external_samplespace

        self.device_manager: DeviceConfiguration
        self.device: QuantumDevice

    def measure_node(self, cluster_status) -> xarray.Dataset:
        """
        Here we attach the measure_node method according to the
        measurement_type: ScheduleNode or ExternalParameterNode or something else
        """
        measurement_type = self.measurement_type(self)
        dataset = measurement_type.measure_node(cluster_status)
        return dataset

    def calibrate(self, data_path, measurement_mode):
        if measurement_mode != MeasurementMode.re_analyse:
            result_dataset = self.measure_node(measurement_mode)
            save_serial_device(self.device, data_path)
            save_dataset(result_dataset, self.name, data_path)
        # After the measurement free the device resources
        close_device_resources(self.device)
        self.post_process(data_path)
        logger.info("analysis completed")

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
        measurement_mode=MeasurementMode.real,
        measurement: Tuple[int, int] = (1, 1),
    ) -> xarray.Dataset:
        """
        Execute a measurement for a node and save the resulting dataset.

        Args:
            compiled_schedule (CompiledSchedule): The compiled schedule to execute.
            measurement_mode (MeasurementMode.real): The status of the measurement mode.
            measurement (tuple): Tuple of (current_measurement, total_measurements).

        Returns:
            xarray.Dataset: The dataset containing the measurement results.
        """

        schedule_duration = self._calculate_schedule_duration(compiled_schedule)
        self._print_measurement_info(schedule_duration, measurement)

        raw_dataset = execute_schedule(
            compiled_schedule,
            schedule_duration,
            self.lab_instr_coordinator,
            measurement_mode,
        )

        if measurement_mode == MeasurementMode.dummy:
            raw_dataset = self.generate_dummy_dataset()
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

    def post_process(self, data_path: Path):
        analysis_kwargs = getattr(self, "analysis_keywords", dict())
        node_analysis: BaseNodeAnalysis = self.analysis_obj(
            self.name, self.redis_fields, **analysis_kwargs
        )
        QOI_dict = node_analysis.analyze_node(data_path)
        for element_id_, qois_ in QOI_dict.items():
            update_redis_trusted_values(
                self.name, element_id_, qoi=qois_, redis_fields=self.redis_fields
            )
        return QOI_dict

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
            dimensions = samplespace_dimensions(samplespace, self.loops)

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
                reshaping = reversed(dimensions)
                data_values = data_values.reshape(*reshaping)
                data_values = np.transpose(data_values)
            else:
                data_values = data_values.reshape(*dimensions, order="F")

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


class QubitNode(BaseNode):
    qubit_qois: list[str] | None = None

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **node_keywords
    ):
        super().__init__(name, **node_keywords)
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.qubit_state = 0  # can be 0 or 1 or 2
        self.plots_per_qubit = 1  # can be 0 or 1 or 2

        if self.qubit_qois is not None:
            self.redis_fields = self.qubit_qois

        self.device = configure_device(
            self.name, qubits=self.all_qubits, couplers=self.couplers
        )

    def precompile(self, schedule_samplespace: dict) -> CompiledSchedule:
        constants.GRID_TIME_TOLERANCE_TIME = 5e-2

        # TODO: put 'tof' out of its misery
        if self.name == "tof":
            return None, 1

        transmons_dict = {
            qubit: self.device.get_element(qubit) for qubit in self.all_qubits
        }
        measurement_class = self.measurement_obj(transmons_dict)
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


class CouplerNode(BaseNode):
    coupler_qois: list[str]

    def __init__(self, name: str, couplers: list[str], **node_keywords):
        super().__init__(name, **node_keywords)
        self.couplers = couplers
        self.edges = couplers
        self.all_qubits = sorted(set(self.get_coupled_qubits()))
        self.plots_per_qubit = 1  # can be 0 or 1 or 2

        if self.coupler_qois is not None:
            self.redis_fields = self.coupler_qois

        self.device = configure_device(
            self.name, qubits=self.all_qubits, couplers=self.couplers
        )

    def get_coupled_qubits(self) -> list:
        coupled_qubits = []
        for coupler in self.couplers:
            qubits = coupler.split(sep="_")
            coupled_qubits.append(qubits[0])
            coupled_qubits.append(qubits[1])
        return coupled_qubits

    def gate_qubit_types_dict(self) -> dict[str, dict]:
        qubit_types_dict = {}
        for coupler in self.couplers:
            q1, q2 = coupler.split("_")

            q1_type = dh.get_legacy("qubit_types")[q1]
            q2_type = dh.get_legacy("qubit_types")[q2]
            if q1_type == "Control" and q2_type == "Target":
                control_qubit = q1
                target_qubit = q2
            elif q1_type == "Target" and q2_type == "Control":
                target_qubit = q1
                control_qubit = q2
            else:
                raise ValueError("Invalid qubit types")
            qubit_types_dict[coupler] = {
                "control_qubit": control_qubit,
                "target_qubit": target_qubit,
            }
        return qubit_types_dict

    def validate(self) -> None:
        all_coupled_qubits = []
        for coupler in self.couplers:
            all_coupled_qubits += coupler.split("_")
        if len(all_coupled_qubits) > len(set(all_coupled_qubits)):
            logger.info("Couplers share qubits")
            raise ValueError("Improper Couplers")

    def transition_frequency(
        self, coupler: str, phase_path: Literal["via_20", "via_02"]
    ) -> float:
        q1, q2 = coupler.split(sep="_")
        q1_f01 = float(REDIS_CONNECTION.hget(f"transmons:{q1}", "clock_freqs:f01"))
        q2_f01 = float(REDIS_CONNECTION.hget(f"transmons:{q2}", "clock_freqs:f01"))
        q1_f12 = float(REDIS_CONNECTION.hget(f"transmons:{q1}", "clock_freqs:f12"))
        q2_f12 = float(REDIS_CONNECTION.hget(f"transmons:{q2}", "clock_freqs:f12"))

        if phase_path == "via_20":
            ac_frequency = np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12))
        elif phase_path == "via_02":
            ac_frequency = np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12))
        else:
            raise ValueError("Invalid Phase path")

        ac_frequency = int(ac_frequency / 1e4) * 1e4
        logger.info(f"{ ac_frequency/1e6 = } MHz for coupler: {coupler}")

        return ac_frequency

    def precompile(self, schedule_samplespace: dict) -> CompiledSchedule:
        constants.GRID_TIME_TOLERANCE_TIME = 5e-2

        transmons_dict = {
            qubit: self.device.get_element(qubit) for qubit in self.all_qubits
        }
        edges_dict = {
            coupler: self.device.get_edge(coupler) for coupler in self.couplers
        }
        measurement_class = self.measurement_obj(transmons_dict, edges_dict)
        schedule = measurement_class.schedule_function(
            **schedule_samplespace, **self.schedule_keywords
        )

        # TODO: Probably the compiler doesn't need to be created every time self.precompile() is called.
        compiler = SerialCompiler(name=f"{self.name}_compiler")

        compilation_config = self.device.generate_compilation_config()
        logger.info("Starting Compiling")
        compiled_schedule = compiler.compile(
            schedule=schedule, config=compilation_config
        )

        return compiled_schedule

    def __str__(self):
        return f"Node representation for {self.name} on couplers {self.couplers}"

    def __format__(self, message):
        return f"Node representation for {self.name} on couplers {self.couplers}"

    def __repr__(self):
        return f"Node({self.name}, {self.couplers})"
