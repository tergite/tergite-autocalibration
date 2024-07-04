"""
Module containing a schedule class for DRAG pulse motzoi parameter calibration.
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler.resources import ClockResource
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.operations.gate_library import Measure, Reset
from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon
import numpy as np


class N_Rabi_Oscillations(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)
        self.transmons = transmons

    def schedule_function(
        self,
        mw_amplitudes_sweep: dict[str, np.ndarray],
        X_repetitions: dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:
        """

        Schedule sequence
            Reset -> DRAG pulse x N times-> Measure
        Step 2 and 3 are repeated X_repetition amount of times

        Parameters
        ----------
        mw_amplitudes
        X_repetition: The amount of times that the DRAG pulse and inverse DRAG pulse are applied
           mw_amplitude: Amplitude of the DRAG pulse for each qubit.
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """
        schedule = Schedule("mltplx_nrabi", repetitions)

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
            mw_pulse_duration = this_transmon.rxy.duration()
            mw_pulse_port = this_transmon.ports.microwave()
            mw_amplitude = this_transmon.rxy.amp180()
            mw_motzoi = this_transmon.rxy.motzoi()

            this_clock = f"{this_qubit}.01"

            mw_amplitudes_values = mw_amplitudes_sweep[this_qubit]
            number_of_amplitudes = len(mw_amplitudes_values)

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new="end"
            )  # To enforce parallelism we refer to the root relaxation

            # The intermediate loop iterates over all amplitude values:
            for x_index, this_x in enumerate(X_values):
                # The inner for loop iterates over all frequency values in the frequency batch:
                for mw_amplitude_index, mw_amplitude_correction in enumerate(
                    mw_amplitudes_values
                ):
                    this_index = x_index * number_of_amplitudes + mw_amplitude_index
                    for _ in range(this_x):
                        schedule.add(
                            DRAGPulse(
                                duration=mw_pulse_duration,
                                G_amp=mw_amplitude + mw_amplitude_correction,
                                D_amp=mw_motzoi,
                                port=mw_pulse_port,
                                clock=this_clock,
                                phase=0,
                            ),
                        )
                    schedule.add(
                        Measure(
                            this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE
                        ),
                    )

                    schedule.add(Reset(this_qubit))

        return schedule
