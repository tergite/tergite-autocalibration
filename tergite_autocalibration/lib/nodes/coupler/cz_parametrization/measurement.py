# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2025
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Amr Osman, 2024
# (C) Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np
from quantify_scheduler import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.control_flow_library import LoopOperation
from quantify_scheduler.operations.gate_library import Reset, X
from quantify_scheduler.operations.pulse_library import (
    IdlePulse,
    SetClockFrequency,
    SoftSquarePulse,
)
from quantify_scheduler.resources import ClockResource

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.extended_coupler_edge import (
    ExtendedCompositeSquareEdge,
)
from tergite_autocalibration.utils.dto.extended_gates import Measure_RO_3state_Opt
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


class CZParametrizationMeasurement(BaseMeasurement):
    def __init__(
        self,
        transmons: dict[str, ExtendedTransmon],
        couplers: dict[str, ExtendedCompositeSquareEdge],
    ):
        super().__init__(transmons, couplers)
        self.transmons = transmons
        self.couplers = couplers

    def cz_parametrization(
        self,
        cz_pulse_frequencies: dict[str, np.ndarray],
        cz_pulse_amplitudes: dict[str, np.ndarray],
        cz_duration: float,
    ) -> Schedule:
        cz_schedule = Schedule("CZ_parametrization")

        root = cz_schedule.add(IdlePulse(4e-9))
        for coupler in self.couplers:
            cz_frequencies = cz_pulse_frequencies[coupler]
            cz_amplitudes = cz_pulse_amplitudes[coupler]
            qubits = coupler.split(sep="_")

            cz_schedule.add_resource(
                ClockResource(
                    name=coupler + ".cz",
                    freq=self.downconvert - cz_frequencies[0],
                )
            )

            cz_schedule.add(
                Reset(*qubits), ref_op=root
            )  # To enforce parallelism we refer to the root operation

            number_of_inners = len(cz_amplitudes)
            for outer_index, cz_frequency in enumerate(cz_frequencies):
                cz_clock = f"{coupler}.cz"
                cz_pulse_port = f"{coupler}:fl"
                cz_schedule.add(
                    SetClockFrequency(
                        clock=cz_clock, clock_freq_new=self.downconvert - cz_frequency
                    ),
                )

                for inner_index, cz_amplitude in enumerate(cz_amplitudes):
                    this_index = outer_index * number_of_inners + inner_index
                    relaxation = cz_schedule.add(Reset(*self.qubits))

                    for this_qubit in self.qubits:
                        operation_11 = cz_schedule.add(X(this_qubit), ref_op=relaxation)

                    # TODO: does this do anything?
                    # cz_schedule.add(ResetClockPhase(clock=self.coupler + ".cz"))

                    flux_pulse = cz_schedule.add(
                        SoftSquarePulse(
                            duration=cz_duration,
                            amp=cz_amplitude,
                            port=cz_pulse_port,
                            clock=cz_clock,
                        ),
                        ref_op=operation_11,
                        # ref_pt="start",
                        # rel_time=28e-9,
                    )

                    for this_qubit in qubits:
                        cz_schedule.add(
                            Measure_RO_3state_Opt(
                                this_qubit,
                                acq_index=this_index,
                                bin_mode=BinMode.APPEND,
                            ),
                            ref_op=flux_pulse,
                        )
        return cz_schedule

    def schedule_function(
        self,
        cz_pulse_frequencies: dict[str, np.ndarray],
        cz_pulse_amplitudes: dict[str, np.ndarray],
        loop_repetitions: int,
        cz_duration: float,
        repetitions: int = 1,
    ) -> Schedule:
        schedule = Schedule("CZ_parametrization", repetitions)

        cz_parametrization = self.cz_parametrization(
            cz_pulse_frequencies, cz_pulse_amplitudes, cz_duration=cz_duration
        )

        schedule.add(IdlePulse(8e-9))
        schedule.add(
            LoopOperation(body=cz_parametrization, repetitions=loop_repetitions)
        )
        schedule.add(IdlePulse(8e-9))

        return schedule
