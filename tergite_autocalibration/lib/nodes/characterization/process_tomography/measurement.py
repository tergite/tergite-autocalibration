# This code is part of Tergite
#
# (C) Copyright Liangyu Chen 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Module containing a schedule class for Ramsey calibration. (1D parameter sweep, for 2D see ramsey_detunings.py)
"""
import itertools

import numpy as np
from quantify_scheduler import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.control_flow_library import Loop
from quantify_scheduler.operations.gate_library import Reset, Rxy, X
from quantify_scheduler.operations.pulse_library import (
    ResetClockPhase,
    IdlePulse,
)
from quantify_scheduler.resources import ClockResource

from tergite_autocalibration.config.settings import REDIS_CONNECTION
from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.extended_coupler_edge import (
    ExtendedCompositeSquareEdge,
)
from tergite_autocalibration.utils.extended_gates import Measure_RO_3state_Opt, Rxy_12
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon


class Process_Tomography(BaseMeasurement):
    def __init__(
        self,
        transmons: dict[str, ExtendedTransmon],
        couplers: dict[str, ExtendedCompositeSquareEdge],
        qubit_state: int = 0,
    ):
        super().__init__(transmons)
        self.transmons = transmons
        self.qubit_state = qubit_state
        self.couplers = couplers

    def schedule_function(
        self,
        ramsey_phases: dict[str, np.ndarray],
        control_ons: dict[str, np.ndarray],
        repetitions: int = 4096,
        opt_cz_pulse_frequency: dict[str, float] = None,
        opt_cz_pulse_duration: dict[str, float] = None,
        opt_cz_pulse_amplitude: dict[str, float] = None,
    ) -> Schedule:
        name = "process_tomography_ssro"
        schedule = Schedule(f"{name}")

        qubit_type_list = ["Control", "Target"]

        all_couplers = list(self.couplers.keys())
        all_qubits = [coupler.split(sep="_") for coupler in all_couplers]
        print("these are all couplers: ", all_couplers)
        print("these are all qubits: ", all_qubits)
        all_qubits = sum(all_qubits, [])

        # The outer for-loop iterates over all qubits:
        shot = Schedule(f"shot")
        shot.add(IdlePulse(16e-9))

        # Initialize ClockResource with the first frequency value
        for this_qubit, this_transmon in self.transmons.items():
            ro_frequency = this_transmon.extended_clock_freqs.readout_3state_opt()
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.ro_3st_opt", freq=ro_frequency)
            )
            mw_frequency_01 = this_transmon.clock_freqs.f01()
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.01", freq=mw_frequency_01)
            )
            mw_frequency_12 = this_transmon.clock_freqs.f12()
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.12", freq=mw_frequency_12)
            )

        for index, this_coupler in enumerate(all_couplers):
            if this_coupler in ["q21_q22", "q22_q23", "q23_q24", "q24_q25"]:
                downconvert = 0
            else:
                downconvert = 4.4e9

        cz_pulse_frequency, cz_pulse_duration, cz_pulse_amplitude = {}, {}, {}
        for coupler in all_couplers:
            qubits = coupler.split(sep="_")
            for this_coupler in all_couplers:
                redis_config = REDIS_CONNECTION.hgetall(f"couplers:{this_coupler}")
                cz_pulse_frequency[this_coupler] = float(
                    redis_config["cz_pulse_frequency"]
                )
                cz_pulse_duration[this_coupler] = float(
                    redis_config["cz_pulse_duration"]
                )
                cz_pulse_amplitude[this_coupler] = float(
                    redis_config["cz_pulse_amplitude"]
                )
                if opt_cz_pulse_amplitude is not None:
                    cz_pulse_amplitude[this_coupler] += opt_cz_pulse_amplitude[
                        this_coupler
                    ]
                if opt_cz_pulse_frequency is not None:
                    cz_pulse_frequency[this_coupler] += opt_cz_pulse_frequency[
                        this_coupler
                    ]
                if opt_cz_pulse_duration is not None:
                    cz_pulse_duration[this_coupler] += opt_cz_pulse_duration[
                        this_coupler
                    ]

        print(f"{cz_pulse_frequency = }")
        print(f"{cz_pulse_duration = }")
        print(f"{cz_pulse_amplitude = }")

        for index, this_coupler in enumerate(all_couplers):
            schedule.add_resource(
                ClockResource(
                    name=f"{this_coupler}.cz",
                    freq=-cz_pulse_frequency[this_coupler] + downconvert,
                )
            )
            shot.add_resource(
                ClockResource(
                    name=f"{this_coupler}.cz",
                    freq=-cz_pulse_frequency[this_coupler] + downconvert,
                )
            )
        # print(ramsey_phases,qubits)

        ramsey_phases_values = ramsey_phases[all_couplers[0]]
        number_of_phases = len(ramsey_phases_values)
        control_on_values = control_ons[all_couplers[0]]

        state = ["g", "e", "+", "-"]
        states = list(itertools.product(state, state))
        test_states = [dict(zip(all_qubits, s)) for s in states]

        rotation = ["I", "x90", "y90"]
        rotations = list(itertools.product(rotation, rotation))
        test_rotations = [dict(zip(all_qubits, s)) for s in rotations]

        for cz_index, control_on in enumerate(control_on_values):
            for ramsey_index, ramsey_phase in enumerate(ramsey_phases_values[:-3]):
                relaxation = shot.add(
                    Reset(*all_qubits), label=f"Reset_{cz_index}_{ramsey_index}"
                )

                test_state = test_states[int(ramsey_phase)]
                # print(f'{test_state = }')
                for this_qubit in all_qubits:
                    if test_state[this_qubit] == "g":
                        end = shot.add(
                            Rxy(0, 0, this_qubit), ref_op=relaxation, ref_pt="end"
                        )
                    elif test_state[this_qubit] == "e":
                        end = shot.add(X(this_qubit), ref_op=relaxation, ref_pt="end")
                    elif test_state[this_qubit] == "+":
                        end = shot.add(
                            Rxy(90, 0, this_qubit), ref_op=relaxation, ref_pt="end"
                        )
                    elif test_state[this_qubit] == "-":
                        end = shot.add(
                            Rxy(90, 90, this_qubit), ref_op=relaxation, ref_pt="end"
                        )

                buffer_start = shot.add(IdlePulse(4e-9), ref_op=end, ref_pt="end")

                for this_coupler in all_couplers:
                    cz_clock = f"{this_coupler}.cz"
                    cz_pulse_port = f"{this_coupler}:fl"

                    reset_phase = shot.add(
                        ResetClockPhase(clock=cz_clock),
                        ref_op=buffer_start,
                        ref_pt="end",
                    )
                    # cz = shot.add(
                    #     SoftSquarePulse(
                    #         duration=cz_pulse_duration[this_coupler],
                    #         # amp=cz_pulse_amplitude[this_coupler],
                    #         amp=0,
                    #         port=cz_pulse_port,
                    #         clock=cz_clock,
                    #     )
                    # )

                buffer_end = shot.add(
                    IdlePulse(4e-9),
                    ref_op=buffer_start,
                    ref_pt="end",
                    rel_time=np.ceil(cz_pulse_duration[this_coupler] * 1e9 / 4) * 4e-9,
                )

                test_rotation = test_rotations[int(control_on)]
                # print(f'{test_state = }')
                for this_qubit in all_qubits:
                    if test_rotation[this_qubit] == "I":
                        end = shot.add(
                            Rxy(0, 0, this_qubit), ref_op=buffer_end, ref_pt="end"
                        )
                    elif test_rotation[this_qubit] == "x90":
                        end = shot.add(
                            Rxy(90, 0, this_qubit), ref_op=buffer_end, ref_pt="end"
                        )
                    elif test_rotation[this_qubit] == "y90":
                        end = shot.add(
                            Rxy(90, 90, this_qubit), ref_op=buffer_end, ref_pt="end"
                        )

                    this_index = cz_index * number_of_phases + ramsey_index
                    shot.add(
                        Measure_RO_3state_Opt(
                            this_qubit, acq_index=this_index, bin_mode=BinMode.APPEND
                        ),
                        # ref_op=end,
                        # ref_pt="end",
                    )

                relaxation = shot.add(
                    Reset(*all_qubits), label=f"Reset_{cz_index}_{ramsey_index}_end"
                )

            # Calibration points
            root_relaxation = shot.add(
                Reset(*all_qubits), label=f"Reset_Calib_{cz_index}"
            )

            for this_qubit in all_qubits:
                qubit_levels = range(self.qubit_state + 1)
                number_of_levels = len(qubit_levels)

                shot.add(
                    Reset(*all_qubits), ref_op=root_relaxation, ref_pt_new="end"
                )  # To enforce parallelism we refer to the root relaxation
                # The intermediate for-loop iterates over all ro_amplitudes:
                # for ampl_indx, ro_amplitude in enumerate(ro_amplitude_values):
                # The inner for-loop iterates over all qubit levels:
                for level_index, state_level in enumerate(qubit_levels):
                    calib_index = this_index + level_index + 1
                    # print(f'{calib_index = }')
                    shot.add(Reset(this_qubit))
                    if state_level == 0:
                        prep = shot.add(IdlePulse(40e-9))
                    elif state_level == 1:
                        prep = shot.add(
                            X(this_qubit),
                        )
                    elif state_level == 2:
                        shot.add(
                            X(this_qubit),
                        )
                        prep = shot.add(
                            Rxy_12(this_qubit),
                        )
                    else:
                        raise ValueError("State Input Error")
                    shot.add(
                        Measure_RO_3state_Opt(
                            this_qubit, acq_index=calib_index, bin_mode=BinMode.APPEND
                        ),
                        ref_op=prep,
                        ref_pt="end",
                    )
                    shot.add(Reset(this_qubit))
        shot.add(IdlePulse(16e-9))

        schedule.add(IdlePulse(16e-9))
        print(schedule.add(shot, control_flow=Loop(repetitions), validate=False))
        schedule.add(IdlePulse(16e-9))
        return schedule
