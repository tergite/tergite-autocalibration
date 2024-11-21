# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.operations.gate_library import Reset, X
from quantify_scheduler.operations.pulse_library import (
    DRAGPulse,
    SetClockFrequency,
    SquarePulse,
)
from quantify_scheduler.resources import ClockResource
from quantify_scheduler.schedules.schedule import Schedule

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon


class RO_frequency_optimization(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon]):
        super().__init__(transmons)
        self.transmons = transmons

    def measure(
        self,
        schedule: Schedule,
        transmon: ExtendedTransmon,
        this_qubit: str,
        acq_index: int,
        acq_cha: int,
        this_ro_clock: str,
    ):
        # TODO: some of these arguments are already contained in the transmon

        measure = transmon.measure
        ro_pulse = schedule.add(
            SquarePulse(
                duration=measure.pulse_duration(),
                amp=measure.pulse_amp(),
                port=transmon.ports.readout(),
                clock=this_ro_clock,
            ),
        )
        schedule.add(
            SSBIntegrationComplex(
                duration=measure.integration_time(),
                port=transmon.ports.readout(),
                clock=this_ro_clock,
                acq_index=acq_index,
                acq_channel=acq_cha,
                bin_mode=BinMode.AVERAGE,
            ),
            ref_op=ro_pulse,
            ref_pt="start",
            rel_time=measure.acq_delay(),
        )

        schedule.add(Reset(this_qubit))

    def measure_first_excited(
        self,
        schedule: Schedule,
        transmon: ExtendedTransmon,
        this_qubit: str,
        acq_index: int,
        acq_cha: int,
        this_ro_clock: str,
    ):
        schedule.add(X(this_qubit))
        self.measure(
            schedule,
            transmon,
            this_qubit,
            acq_index,
            acq_cha,
            this_ro_clock,
        )

    def measure_second_excited(
        self,
        schedule: Schedule,
        transmon: ExtendedTransmon,
        this_qubit: str,
        acq_index: int,
        acq_cha: int,
        this_ro_clock: str,
        this_mw_clock: str,
    ):
        # repeat for when the qubit is at |2>
        schedule.add(X(this_qubit))
        schedule.add(
            DRAGPulse(
                duration=transmon.rxy.duration(),
                G_amp=transmon.r12.ef_amp180(),
                D_amp=0,
                port=transmon.ports.microwave(),
                clock=this_mw_clock,
                phase=0,
            ),
        )
        self.measure(
            schedule,
            transmon,
            this_qubit,
            acq_index,
            acq_cha,
            this_ro_clock,
        )

        schedule.add(Reset(this_qubit))

    def schedule_function(
        self,
        ro_opt_frequencies: dict[str, np.ndarray],
        qubit_states: dict[str, list[int]],
        repetitions: int = 1024,
    ) -> Schedule:
        schedule = Schedule("multiplexed_ro_frequency_optimization", repetitions)

        qubits = self.transmons.keys()

        # Initialize the clock for each qubit
        if len(qubit_states[list(qubits)[0]]) == 2:
            ro_str = "ro_2st_opt"
        elif len(qubit_states[list(qubits)[0]]) == 3:
            ro_str = "ro_3st_opt"
        else:
            raise ValueError("invalid number of states")

        # Initialize ClockResource with the first frequency value
        for this_qubit, ro_array_val in ro_opt_frequencies.items():
            this_ro_clock = f"{this_qubit}." + ro_str
            schedule.add_resource(
                ClockResource(name=this_ro_clock, freq=ro_array_val[0])
            )

        if len(qubit_states[list(qubits)[0]]) == 3:
            for this_qubit, this_transmon in self.transmons.items():
                mw_frequency_12 = this_transmon.clock_freqs.f12()
                this_clock = f"{this_qubit}.12"
                schedule.add_resource(
                    ClockResource(name=this_clock, freq=mw_frequency_12)
                )

        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The first for loop iterates over all qubits:
        for acq_cha, (this_qubit, ro_f_values) in enumerate(ro_opt_frequencies.items()):
            # unpack the static parameters
            this_transmon = self.transmons[this_qubit]

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new="end"
            )  # To enforce parallelism we refer to the root relaxation

            this_ro_clock = f"{this_qubit}." + ro_str

            if len(qubit_states[list(qubits)[0]]) == 3:
                this_mw_clock = f"{this_qubit}.12"

            this_qubit_states = qubit_states[this_qubit]

            number_of_frequencies = len(ro_f_values)

            for acq_index, ro_frequency in enumerate(ro_f_values):
                schedule.add(
                    SetClockFrequency(clock=this_ro_clock, clock_freq_new=ro_frequency),
                )

                # The third for loop iterates over all qubit states
                for qubit_state in this_qubit_states:
                    if qubit_state == 0:
                        this_index = acq_index
                        self.measure(
                            schedule,
                            this_transmon,
                            this_qubit,
                            this_index,
                            acq_cha,
                            this_ro_clock,
                        )
                    # repeat for when the qubit is at |1>
                    elif qubit_state == 1:
                        this_index = acq_index + number_of_frequencies
                        self.measure_first_excited(
                            schedule,
                            this_transmon,
                            this_qubit,
                            this_index,
                            acq_cha,
                            this_ro_clock,
                        )
                    # repeat for when the qubit is at |2>
                    elif qubit_state == 2:
                        this_index = acq_index + 2 * number_of_frequencies
                        self.measure_second_excited(
                            schedule,
                            this_transmon,
                            this_qubit,
                            this_index,
                            acq_cha,
                            this_ro_clock,
                            this_mw_clock,
                        )

        return schedule
