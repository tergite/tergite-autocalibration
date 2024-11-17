# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Module containing a schedule class for randomized benchmarking measurement.
"""
import numpy as np
from quantify_scheduler.operations.gate_library import Reset, Rxy, X
from quantify_scheduler.operations.pulse_library import IdlePulse
from quantify_scheduler.schedules.schedule import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.control_flow_library import Loop
import tergite_autocalibration.utils.clifford_elements_decomposition as cliffords
from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.extended_gates import Measure_RO_3state_Opt, Rxy_12
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon
from quantify_scheduler.resources import ClockResource


class Randomized_Benchmarking_SSRO(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)
        self.transmons = transmons
        self.qubit_state = qubit_state

    def schedule_function(
        self,
        seeds: int,
        number_of_cliffords: dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:
        """
        Generate a schedule for performing a randomized benchmarking test using Clifford gates.
        The goal is to get a measure of the total error of the calibrated qubits.

        Schedule sequence
            Reset -> Apply Clifford operations-> Apply inverse of all Clifford operations -> Measure

        Parameters
        ----------
        repetitions
            The amount of times the Schedule will be repeated.
        **number_of_cliffords_operations
            The number of random Clifford operations applied and then inverted on each qubit state.
            This parameter is swept over.

        Returns
        -------
        :
            An experiment schedule.
        """
        schedule = Schedule("multiplexed_randomized_benchmarking")

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

        qubits = list(self.transmons.keys())

        root_relaxation = shot.add(Reset(*qubits), label="Start")

        # The first for loop iterates over all qubits:
        # for this_qubit, clifford_sequence_lengths in number_of_cliffords.items():
        clifford_sequence_lengths = list(number_of_cliffords.values())[0]

        # The inner for loop iterates over the random clifford sequence lengths
        for this_qubit, clifford_sequence_lengths in number_of_cliffords.items():
            all_cliffords = len(cliffords.XY_decompositions)
            seed = seeds[this_qubit]

            rng = np.random.default_rng(seed)

            reset = shot.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt="end"
            )  # To enforce parallelism we refer to the root relaxation

            # The inner for loop iterates over the random clifford sequence lengths
            for acq_index, this_number_of_cliffords in enumerate(
                clifford_sequence_lengths[:-3]
            ):
                # schedule.add(X(this_qubit))
                random_sequence = rng.integers(
                    all_cliffords, size=this_number_of_cliffords
                )

                for sequence_index in random_sequence:
                    physical_gates = cliffords.XY_decompositions[sequence_index]
                    for gate_angles in physical_gates.values():
                        theta = gate_angles["theta"]
                        phi = gate_angles["phi"]
                        shot.add(Rxy(qubit=this_qubit, theta=theta, phi=phi))

                recovery_index, recovery_XY_operations = cliffords.reversing_XY_matrix(
                    random_sequence
                )

                for gate_angles in recovery_XY_operations.values():
                    theta = gate_angles["theta"]
                    phi = gate_angles["phi"]
                    recovery_gate = shot.add(
                        Rxy(qubit=this_qubit, theta=theta, phi=phi)
                    )
                # buffer = shot.add(IdlePulse(40e-9))
                shot.add(
                    Measure_RO_3state_Opt(
                        this_qubit, acq_index=acq_index, bin_mode=BinMode.APPEND
                    ),
                    ref_op=recovery_gate,
                    ref_pt="end",
                )

                shot.add(Reset(this_qubit))

        root_relaxation = shot.add(Reset(*qubits))

        for this_qubit in qubits:
            qubit_levels = range(self.qubit_state + 1)
            number_of_levels = len(qubit_levels)

            shot.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new="end"
            )  # To enforce parallelism we refer to the root relaxation

            # The intermediate for-loop iterates over all ro_amplitudes:
            # for ampl_indx, ro_amplitude in enumerate(ro_amplitude_values):
            # The inner for-loop iterates over all qubit levels:
            for level_index, state_level in enumerate(qubit_levels):
                calib_index = acq_index + level_index + 1
                # print(f'{calib_index = }')
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

        schedule.add(IdlePulse(16e-9))
        print(schedule.add(shot, control_flow=Loop(repetitions)))
        schedule.add(IdlePulse(16e-9))

        return schedule
