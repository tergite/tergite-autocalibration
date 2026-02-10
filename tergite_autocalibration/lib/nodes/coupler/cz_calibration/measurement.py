# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024, 2025, 2026
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Chalmers Next Labs AB 2024, 2025, 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from typing import Tuple

import numpy as np
from quantify_scheduler import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.control_flow_library import Loop
from quantify_scheduler.operations.gate_library import X90, Reset, Rxy, X
from quantify_scheduler.operations.pulse_library import (
    IdlePulse,
    ResetClockPhase,
    SoftSquarePulse,
)
from quantify_scheduler.resources import ClockResource
from quantify_scheduler.schedules.schedule import LoopOperation

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.extended_coupler_edge import (
    ExtendedCompositeSquareEdge,
)
from tergite_autocalibration.utils.dto.extended_gates import Measure_RO_3state_Opt
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


class CZ_CalibrationMeasurement(BaseMeasurement):
    def __init__(
        self,
        transmons: dict[str, ExtendedTransmon],
        couplers: dict[str, ExtendedCompositeSquareEdge],
    ):
        super().__init__(transmons)
        self.transmons = transmons
        self.couplers = couplers
        self.downconvert = 4.4e9

    def ro_shot(
        self,
        ramsey_phases: dict[str, np.ndarray],
        control_ons: dict[str, np.ndarray],
        cz_working_points: dict[str, Tuple[float, float]],
        coupler_dict: dict[str, dict],
    ):
        shot = Schedule("cz_calibration_shot", repetitions=1)

        qubits = self.transmons.keys()
        root = shot.add(IdlePulse(4e-9))

        for this_coupler in self.couplers:

            cz_frequency, cz_duration = cz_working_points[this_coupler]
            control_on_values = control_ons[this_coupler]
            control_qubit = coupler_dict[this_coupler]["control_qubit"]
            target_qubit = coupler_dict[this_coupler]["target_qubit"]

            # unpack the static parameters:
            this_edge = self.couplers[this_coupler]
            cz_amplitude = this_edge.cz.square_amp()
            cz_clock = f"{this_coupler}.cz"
            cz_pulse_port = f"{this_coupler}:fl"

            # Initialize the clock at the first frequency value
            shot.add_resource(
                ClockResource(
                    name=cz_clock,
                    freq=-cz_frequency + self.downconvert,
                )
            )

            connected_qubits = this_coupler.split("_")
            first_qubit = connected_qubits[0]
            first_transmon = self.transmons[first_qubit]
            r_xy_duration = first_transmon.rxy.duration()

            shot.add(
                Reset(*qubits), ref_op=root
            )  # To enforce parallelism we refer to the root operation

            ramsey_phases_values = ramsey_phases[target_qubit]
            number_of_inners = len(ramsey_phases_values)
            for outer_index, control_on in enumerate(control_on_values):

                for inner_index, ramsey_phase in enumerate(ramsey_phases_values):
                    starting_op = shot.add(IdlePulse(4e-9))

                    this_index = outer_index * number_of_inners + inner_index
                    initial = shot.add(X90(target_qubit), ref_op=starting_op)
                    if control_on:
                        initial = shot.add(X(control_qubit), ref_op=starting_op)
                    else:
                        initial = shot.add(IdlePulse(r_xy_duration), ref_op=starting_op)

                    # shot.add(IdlePulse(20e-9))
                    shot.add(ResetClockPhase(clock=cz_clock), ref_op=initial)
                    # shot.add(IdlePulse(20e-9))
                    cz = shot.add(
                        SoftSquarePulse(
                            duration=cz_duration,
                            amp=cz_amplitude,
                            port=cz_pulse_port,
                            clock=cz_clock,
                        ),
                    )

                    final = shot.add(
                        Rxy(theta=90, phi=ramsey_phase, qubit=target_qubit),
                        ref_op=cz,
                    )
                    if control_on:
                        final = shot.add(X(control_qubit), ref_op=cz)
                    else:
                        final = shot.add(IdlePulse(r_xy_duration), ref_op=cz)

                    shot.add(
                        Measure_RO_3state_Opt(
                            control_qubit,
                            acq_index=this_index,
                            bin_mode=BinMode.APPEND,
                        ),
                        ref_op=final,
                    )
                    shot.add(
                        Measure_RO_3state_Opt(
                            target_qubit,
                            acq_index=this_index,
                            bin_mode=BinMode.APPEND,
                        ),
                        ref_op=final,
                    )

                    shot.add(Reset(control_qubit, target_qubit))

        return shot

    def schedule_function(
        self,
        ramsey_phases: dict[str, np.ndarray],
        control_ons: dict[str, np.ndarray],
        loop_repetitions: int,
        working_points: dict[str, Tuple[float, float]],
        coupler_dict: dict[str, dict],
        repetitions: int = 1,
    ) -> Schedule:

        schedule = Schedule("cz_calibration", repetitions)

        cz_phase_shot = self.ro_shot(
            ramsey_phases,
            control_ons,
            cz_working_points=working_points,
            coupler_dict=coupler_dict,
        )

        schedule.add(IdlePulse(16e-9))
        schedule.add(LoopOperation(body=cz_phase_shot, repetitions=loop_repetitions))
        schedule.add(IdlePulse(16e-9))
        return schedule
