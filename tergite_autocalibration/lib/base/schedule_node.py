import json

import numpy as np
from quantify_scheduler.instrument_coordinator.utility import xarray

from tergite_autocalibration.config.settings import HARDWARE_CONFIG
from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.lib.utils.device import (
    configure_device,
    save_serial_device,
)
from tergite_autocalibration.lib.utils.validators import (
    MixedSamplespace,
    Samplespace,
    SimpleSamplespace,
    get_batched_coord,
    get_number_of_batches,
    reduce_batch,
)
from tergite_autocalibration.utils.measurement_utils import reduce_samplespace

# TODO: maybe this deosn't belong here
with open(HARDWARE_CONFIG) as hw:
    hw_config = json.load(hw)


class ScheduleNode(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, schedule_keywords=schedule_keywords)

    @property
    def outer_schedule_dimensions(self) -> int:
        """
        size of outer samplespace E.g. in
        self.outer_samplespace = {
            'cz_amplitudes': {'q06_q07': np.array([1e-6, 2e-6, 3e-6, 4e-6])}
        }
        the external_dimensions is 4
        """
        outer_settable_quantities = self.outer_schedule_samplespace.keys()

        if len(outer_settable_quantities) > 1:
            raise NotImplementedError("Multidimensional Outer Samplespace")

        settable = list(outer_settable_quantities)[0]
        measured_elements = self.outer_schedule_samplespace[settable].keys()
        first_element = list(measured_elements)[0]

        dimensions = len(self.outer_schedule_samplespace[settable][first_element])
        return dimensions

    def measure_node(self, data_path, cluster_status) -> xarray.Dataset:
        """
        Measurements that involve only schedule parametres
        """
        result_dataset = self.measure_schedule_node(
            data_path,
            cluster_status=cluster_status,
        )

        return result_dataset

    def measure_schedule_node(
        self,
        data_path,
        cluster_status,
    ) -> xarray.Dataset:

        qubits = self.all_qubits
        couplers = self.couplers
        device = configure_device(self.name, qubits, couplers)
        device.hardware_config(hw_config)
        save_serial_device(self.name, device, data_path)

        if self.outer_schedule_samplespace == {}:
            validated_samplespace = Samplespace(self.schedule_samplespace)

            if isinstance(validated_samplespace.root, SimpleSamplespace):
                """
                This correspond to simple cluster schedules
                """
                compiled_schedule = self.precompile(device)
                result_dataset = self.measure_compiled_schedule(
                    compiled_schedule,
                    cluster_status=cluster_status,
                )
            elif isinstance(validated_samplespace.root, MixedSamplespace):
                """
                This correspond to schedules with instructions number
                greater than the instructions limit of the QCM_RF
                """
                number_of_batches = get_number_of_batches(self.samplespace)
                batched_coord = get_batched_coord(self.samplespace)
                result_dataset = xarray.Dataset()
                for batch_index in range(number_of_batches):
                    self.samplespace = reduce_batch(self.samplespace, batch_index)
                    compiled_schedule = self.precompile(device)
                    ds = self.measure_compiled_schedule(
                        compiled_schedule,
                        cluster_status=cluster_status,
                        measurement=(batch_index, number_of_batches),
                    )
                    result_dataset = xarray.concat(
                        [ds, result_dataset], dim=batched_coord
                    )

        else:
            """
            This correspond to schedules where the measurement points
            are more than the memory limit of the QRM_RF.
            For example large single shots measurements
            """
            iterations = self.outer_schedule_dimensions
            outer_dim = list(self.outer_schedule_samplespace.keys())[0]

            result_dataset = xarray.Dataset()

            for current_iteration in range(iterations):
                self.reduced_outer_samplespace = reduce_samplespace(
                    current_iteration, self.outer_schedule_samplespace
                )
                element_dict = list(self.reduced_outer_samplespace.values())[0]
                current_value = list(element_dict.values())[0]

                compiled_schedule = self.precompile(device)

                ds = self.measure_compiled_schedule(
                    compiled_schedule,
                    cluster_status,
                    measurement=(current_iteration, iterations),
                )
                ds = ds.expand_dims({outer_dim: np.array([current_value])})
                result_dataset = xarray.merge([ds, result_dataset])

        device.close()

        return result_dataset
