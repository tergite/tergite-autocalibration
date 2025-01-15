# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Module containing a schedule class for punchout (readout amplitude) calibration.
"""
import numpy as np
from quantify_scheduler import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.operations.gate_library import Reset
from quantify_scheduler.operations.pulse_library import SquarePulse, SetClockFrequency
from quantify_scheduler.resources import ClockResource

from tergite_autocalibration.lib.base.measurement import BaseMeasurement


class PunchoutMeasurement(BaseMeasurement):
    def __init__(self, transmons, qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

    def schedule_function(
        self,
        ro_frequencies: dict[str, np.ndarray],
        ro_amplitudes: dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:
        schedule = Schedule("mltplx_punchout", repetitions)

        qubits = self.transmons.keys()

        # Initialize the clock for each qubit
        for this_qubit, ro_array_val in ro_frequencies.items():
            # Initialize ClockResource with the first frequency value
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.ro", freq=ro_array_val[0])
            )

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer loop, iterates over all qubits
        for acq_cha, (this_qubit, ro_amplitude_values) in enumerate(
            ro_amplitudes.items()
        ):
            # unpack the static parameters
            this_transmon = self.transmons[this_qubit]
            ro_pulse_duration = this_transmon.measure.pulse_duration()
            acquisition_delay = this_transmon.measure.acq_delay()
            integration_time = this_transmon.measure.integration_time()
            ro_port = this_transmon.ports.readout()

            this_clock = f"{this_qubit}.ro"

            frequency_values = ro_frequencies[this_qubit]
            number_of_freqs = len(frequency_values)

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new="end"
            )  # To enforce parallelism we refer to the root relaxation

            # The intermediate loop, iterates over all ro_amplitudes
            for ampl_indx, ro_amplitude in enumerate(ro_amplitude_values):
                # The inner for loop iterates over all frequency values in the frequency batch:
                for acq_index, ro_freq in enumerate(frequency_values):
                    # for acq_index, ro_freq in enumerate(ro_frequencies[this_qubit]):
                    this_index = ampl_indx * number_of_freqs + acq_index

                    schedule.add(
                        SetClockFrequency(clock=this_clock, clock_freq_new=ro_freq),
                    )

                    schedule.add(
                        SquarePulse(
                            duration=ro_pulse_duration,
                            amp=ro_amplitude,
                            port=ro_port,
                            clock=this_clock,
                        ),
                        ref_pt="end",
                    )

                    schedule.add(
                        SSBIntegrationComplex(
                            duration=integration_time,
                            port=ro_port,
                            clock=this_clock,
                            acq_index=this_index,
                            acq_channel=acq_cha,
                            bin_mode=BinMode.AVERAGE,
                        ),
                        ref_pt="start",
                        rel_time=acquisition_delay,
                        label=f"acquisition_{this_qubit}_{this_index}",
                    )

                    schedule.add(Reset(this_qubit))

        return schedule
