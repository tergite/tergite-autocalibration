"""
Module containing a schedule class for DRAG pulse motzoi parameter calibration.
"""
from __future__ import annotations
from quantify_scheduler.enums import BinMode
from quantify_scheduler.resources import ClockResource
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.operations.gate_library import Measure, Reset
from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon
import numpy as np


class Motzoi_parameter(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state=0):
        super().__init__(transmons)
        self.transmons = transmons

    def schedule_function(
        self,
        mw_motzois: dict[str, np.ndarray],
        X_repetitions: int | dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:
        """
        Generate a schedule for a DRAG pulse calibration measurement that gives the optimized motzoi parameter.
        This calibrates the drive pulse as to account for errors caused by higher order excitations of the qubits.

        Schedule sequence
            Reset -> DRAG pulse -> Inverse DRAG pulse -> Measure
        Step 2 and 3 are repeated X_repetition amount of times


        Parameters
        ----------
        repetitions
            The amount of times the Schedule will be repeated.
        mw_motzois
            2D sweeping parameter arrays.
        X_repetition: The amount of times that the DRAG pulse and inverse DRAG pulse are applied
            mw_motzoi: The mozoi parameter values of the DRAG (and inverse DRAG) pulses.

        Returns
        -------
        :
            An experiment schedule.
        """
        schedule = Schedule("mltplx_motzoi", repetitions)

        qubits = self.transmons.keys()

        for this_qubit, this_transmon in self.transmons.items():
            mw_frequency = this_transmon.clock_freqs.f01()
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.01", freq=mw_frequency)
            )

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer loop, iterates over all qubits
        for this_qubit, X_values in X_repetitions.items():
            this_transmon = self.transmons[this_qubit]
            mw_amplitude = this_transmon.rxy.amp180()
            mw_pulse_duration = this_transmon.rxy.duration()
            mw_pulse_port = this_transmon.ports.microwave()

            this_clock = f"{this_qubit}.01"

            motzoi_parameter_values = mw_motzois[this_qubit]
            number_of_motzois = len(motzoi_parameter_values)

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new="end"
            )  # To enforce parallelism we refer to the root relaxation

            # The intermediate loop iterates over all numbers of X pulses
            for x_index, this_x in enumerate(X_values):
                # The inner for loop iterates over all motzoi values
                for motzoi_index, mw_motzoi in enumerate(motzoi_parameter_values):
                    this_index = x_index * number_of_motzois + motzoi_index
                    for _ in range(this_x):
                        schedule.add(
                            DRAGPulse(
                                duration=mw_pulse_duration,
                                G_amp=mw_amplitude,
                                D_amp=mw_motzoi,
                                port=mw_pulse_port,
                                clock=this_clock,
                                phase=0,
                            ),
                        )
                        # inversion pulse requires 180 deg phase
                        schedule.add(
                            DRAGPulse(
                                duration=mw_pulse_duration,
                                G_amp=mw_amplitude,
                                D_amp=mw_motzoi,
                                port=mw_pulse_port,
                                clock=this_clock,
                                phase=180,
                            ),
                        )

                    schedule.add(
                        Measure(
                            this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE
                        ),
                    )

                    schedule.add(Reset(this_qubit))

        return schedule
