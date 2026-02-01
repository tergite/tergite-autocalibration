# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024, 2025, 2026
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Chalmers Next Labs 2024, 2025, 2026
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
from quantify_scheduler.operations.control_flow_library import Loop
from quantify_scheduler.operations.gate_library import X90, Reset, Rxy
from quantify_scheduler.operations.pulse_library import IdlePulse, SoftSquarePulse
from quantify_scheduler.resources import ClockResource
from quantify_scheduler.schedules.schedule import LoopOperation

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.extended_coupler_edge import (
    ExtendedCompositeSquareEdge,
)
from tergite_autocalibration.utils.dto.extended_gates import Measure_RO_3state_Opt
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


class CZ_DynamicPhaseMeasurement(BaseMeasurement):
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
        local_phases: dict[str, np.ndarray],
        swap: dict[str, np.ndarray],
        cz_gate_modes: dict[str, np.ndarray],
        coupler_dict: dict[str, dict],
    ):
        shot = Schedule("cz_local_phase_shot", repetitions=1)

        qubits = self.transmons.keys()
        root_relaxation = shot.add(IdlePulse(4e-9))

        for this_coupler in self.couplers:

            control_qubit = coupler_dict[this_coupler]["control_qubit"]
            target_qubit = coupler_dict[this_coupler]["target_qubit"]
            swap_modes = swap[this_coupler]
            gate_modes = cz_gate_modes[this_coupler]

            # unpack the static parameters:
            this_edge = self.couplers[this_coupler]
            cz_frequency = this_edge.clock_freqs.cz_freq()
            cz_amplitude = this_edge.cz.square_amp()
            cz_duration = this_edge.cz.square_duration()
            print(f"{ cz_duration = }")
            print(f"{ cz_frequency = }")
            print(f"{ cz_amplitude = }")
            cz_clock = f"{this_coupler}.cz"
            cz_pulse_port = f"{this_coupler}:fl"

            # Initialize the clock at the first frequency value
            shot.add_resource(
                ClockResource(
                    name=cz_clock,
                    freq=-cz_frequency + self.downconvert,
                )
            )

            shot.add(
                Reset(*qubits), ref_op=root_relaxation
            )  # To enforce parallelism we refer to the root relaxation

            for outer_index, swap_mode in enumerate(swap_modes):
                if swap_mode:
                    control_qubit, target_qubit = target_qubit, control_qubit

                local_phases_values = local_phases[target_qubit]
                number_of_inners = len(local_phases_values)

                number_of_intermediates = len(gate_modes)
                for intermediate_index, gate_mode in enumerate(gate_modes):

                    for inner_index, local_phase in enumerate(local_phases_values):
                        starting_op = shot.add(IdlePulse(4e-9))

                        this_index = (
                            outer_index * (number_of_intermediates * number_of_inners)
                            + intermediate_index * number_of_inners
                            + inner_index
                        )

                        shot.add(X90(target_qubit), ref_op=starting_op)

                        if gate_mode:
                            shot.add(
                                SoftSquarePulse(
                                    duration=cz_duration,
                                    amp=cz_amplitude,
                                    port=cz_pulse_port,
                                    clock=cz_clock,
                                ),
                            )
                        else:
                            shot.add(IdlePulse(cz_duration))

                        final = shot.add(
                            Rxy(theta=90, phi=local_phase, qubit=target_qubit)
                        )

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
        local_phases: dict[str, np.ndarray],
        swap: dict[str, np.ndarray],
        gate_modes: dict[str, np.ndarray],
        loop_repetitions: int,
        coupler_dict: dict[str, dict],
        repetitions: int = 1,
    ) -> Schedule:

        schedule = Schedule("CZ_local_phases", repetitions)

        local_phase_shot = self.ro_shot(
            local_phases=local_phases,
            swap=swap,
            cz_gate_modes=gate_modes,
            coupler_dict=coupler_dict,
        )

        schedule.add(IdlePulse(16e-9))
        schedule.add(LoopOperation(body=local_phase_shot, repetitions=loop_repetitions))
        schedule.add(IdlePulse(16e-9))
        return schedule
