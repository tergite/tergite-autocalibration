"""
Module containing a schedule class for Rabi calibration.
"""
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon
from tergite_autocalibration.lib.base.measurement import BaseMeasurement


class CW_Two_Tones_Spectroscopy(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

    def schedule_function(self, repetitions: int = 1024, **kwargs) -> Schedule:
        """
        ***************************************************
        This is just a measurement operation.
        The cw qubit tone is handeled as an external parameter.
        ***************************************************

        Schedule sequence
            Reset -> Measure
        Parameters

        ----------
        repetitions
            The amount of times the Schedule will be repeated.

        """

        schedule = Schedule("cw_qubit_spectroscopy", repetitions)

        qubits = self.transmons.keys()

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        for this_qubit in qubits:
            schedule.add(
                Reset(this_qubit), ref_op=root_relaxation, ref_pt="end"
            )  # To enforce parallelism we refer to the root relaxation

            schedule.add(
                Measure(this_qubit),
            )

        return schedule
