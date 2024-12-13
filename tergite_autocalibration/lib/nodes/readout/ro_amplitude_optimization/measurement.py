# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
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
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.operations.control_flow_library import Loop
from quantify_scheduler.operations.gate_library import Reset, X
from quantify_scheduler.operations.pulse_library import (
    DRAGPulse,
    IdlePulse,
    SquarePulse,
)
from quantify_scheduler.resources import ClockResource

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


class RO_amplitude_optimization(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon]):
        super().__init__(transmons)

        self.transmons = transmons

    def ro_shot(
        self,
        ro_amplitudes: dict[str, np.ndarray],
        qubit_states: dict[str, np.ndarray],
        qubit_state: int = 1,
    ):
        shot = Schedule("ro_amplitude_optimization_shots", repetitions=1)

        qubits = self.transmons.keys()

        # Initialize ClockResource with the first frequency value
        ro_str = "ro_2st_opt"
        if qubit_state == 2:
            ro_str = "ro_3st_opt"

        for this_qubit, this_transmon in self.transmons.items():
            this_ro_clock = f"{this_qubit}." + ro_str
            mw_frequency_01 = this_transmon.clock_freqs.f01()
            if qubit_state == 1:
                ro_frequency = this_transmon.extended_clock_freqs.readout_2state_opt()
            if qubit_state == 2:
                ro_frequency = this_transmon.extended_clock_freqs.readout_3state_opt()
                mw_frequency_12 = this_transmon.clock_freqs.f12()
                this_clock = f"{this_qubit}.12"
                shot.add_resource(ClockResource(name=this_clock, freq=mw_frequency_12))

            shot.add_resource(ClockResource(name=this_ro_clock, freq=ro_frequency))
            shot.add_resource(
                ClockResource(name=f"{this_qubit}.01", freq=mw_frequency_01)
            )

        # The outer for-loop iterates over all qubits:
        root_relaxation = shot.add(Reset(*qubits), label="Reset")

        for acq_cha, (this_qubit, ro_amplitude_values) in enumerate(
            ro_amplitudes.items()
        ):
            # unpack the static parameters:
            this_transmon = self.transmons[this_qubit]
            ro_pulse_duration = this_transmon.measure.pulse_duration()
            mw_ef_amp180 = this_transmon.r12.ef_amp180()
            mw_pulse_duration = this_transmon.rxy.duration()
            mw_pulse_port = this_transmon.ports.microwave()
            acquisition_delay = this_transmon.measure.acq_delay()
            integration_time = this_transmon.measure.integration_time()
            ro_port = this_transmon.ports.readout()

            this_ro_clock = f"{this_qubit}." + ro_str
            this_clock = f"{this_qubit}.01"
            this_12_clock = f"{this_qubit}.12"

            qubit_levels = qubit_states[this_qubit]
            number_of_levels = len(qubit_levels)

            # To enforce parallelism we refer to the root relaxation
            shot.add(Reset(*qubits), ref_op=root_relaxation, ref_pt_new="end")

            # The intermediate for-loop iterates over all ro_amplitudes:
            for ampl_indx, ro_amplitude in enumerate(ro_amplitude_values):
                # The inner for-loop iterates over all qubit levels:
                for level_index, state_level in enumerate(qubit_levels):
                    this_index = ampl_indx * number_of_levels + level_index

                    if state_level == 0:
                        prep = shot.add(IdlePulse(mw_pulse_duration))

                    elif state_level == 1:
                        prep = shot.add(X(this_qubit))

                    elif state_level == 2:
                        shot.add(X(this_qubit))

                        prep = shot.add(
                            DRAGPulse(
                                duration=mw_pulse_duration,
                                G_amp=mw_ef_amp180,
                                D_amp=0,
                                port=mw_pulse_port,
                                clock=this_12_clock,
                                phase=0,
                            ),
                        )
                    else:
                        raise ValueError("State Input Error")

                    ro_pulse = shot.add(
                        SquarePulse(
                            duration=ro_pulse_duration,
                            amp=ro_amplitude,
                            port=ro_port,
                            clock=this_ro_clock,
                        ),
                        ref_op=prep,
                        ref_pt="end",
                        # rel_time=100e-9,
                    )

                    shot.add(
                        SSBIntegrationComplex(
                            duration=integration_time,
                            port=ro_port,
                            clock=this_ro_clock,
                            acq_index=this_index,
                            acq_channel=acq_cha,
                            bin_mode=BinMode.APPEND,
                        ),
                        ref_op=ro_pulse,
                        ref_pt="start",
                        rel_time=acquisition_delay,
                    )

                    shot.add(Reset(this_qubit))
        shot.add(IdlePulse(20e-9))
        return shot

    def schedule_function(
        self,
        ro_amplitudes: dict[str, np.ndarray],
        qubit_states: dict[str, np.ndarray],
        loop_repetitions: int,
        qubit_state: int = 1,
    ) -> Schedule:
        schedule = Schedule("RO_amplitude_optimization", repetitions=1)
        ro_shot_schedule = self.ro_shot(ro_amplitudes, qubit_states, qubit_state)

        schedule.add(ro_shot_schedule, control_flow=Loop(loop_repetitions))
        schedule.add(IdlePulse(20e-9))
        return schedule
