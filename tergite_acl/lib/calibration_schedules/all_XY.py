from quantify_scheduler.resources import ClockResource
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse, IdlePulse
from quantify_scheduler.operations.gate_library import Measure, Reset, X, Y, X90, Y90
from tergite_acl.utils.extended_transmon_element import ExtendedTransmon, Measure_RO1
from tergite_acl.lib.measurement_base import Measurement
import numpy as np


def return_to_ground(qubit: str) -> Schedule:
    XY_to_ground = Schedule("XY_to_ground")
    #1
    XY_to_ground.add(IdlePulse(28e-9))
    XY_to_ground.add(IdlePulse(28e-9))
    XY_to_ground.add(Measure(qubit))
    XY_to_ground.add(Reset(qubit))
    #2
    XY_to_ground.add(X(qubit))
    XY_to_ground.add(X(qubit))
    XY_to_ground.add(Measure(qubit))
    XY_to_ground.add(Reset(qubit))
    #3
    XY_to_ground.add(Y(qubit))
    XY_to_ground.add(Y(qubit))
    XY_to_ground.add(Measure(qubit))
    XY_to_ground.add(Reset(qubit))
    #4
    XY_to_ground.add(X(qubit))
    XY_to_ground.add(Y(qubit))
    XY_to_ground.add(Measure(qubit))
    XY_to_ground.add(Reset(qubit))
    #5
    XY_to_ground.add(Y(qubit))
    XY_to_ground.add(X(qubit))
    XY_to_ground.add(Measure(qubit))
    XY_to_ground.add(Reset(qubit))

    return XY_to_ground

def return_to_equator(qubit: str) -> Schedule:
    XY_to_equator = Schedule("all_XY")
    #6
    XY_to_equator.add(X90(qubit))
    XY_to_equator.add(IdlePulse(28e-9))
    XY_to_equator.add(Measure(qubit))
    XY_to_equator.add(Reset(qubit))
    #7
    XY_to_equator.add(Y90(qubit))
    XY_to_equator.add(IdlePulse(28e-9))
    XY_to_equator.add(Measure(qubit))
    XY_to_equator.add(Reset(qubit))
    #8
    XY_to_equator.add(X90(qubit))
    XY_to_equator.add(Y90(qubit))
    XY_to_equator.add(Measure(qubit))
    XY_to_equator.add(Reset(qubit))
    #9
    XY_to_equator.add(Y90(qubit))
    XY_to_equator.add(X90(qubit))
    XY_to_equator.add(Measure(qubit))
    XY_to_equator.add(Reset(qubit))
    #10
    XY_to_equator.add(X90(qubit))
    XY_to_equator.add(Y(qubit))
    XY_to_equator.add(Measure(qubit))
    XY_to_equator.add(Reset(qubit))
    #11
    XY_to_equator.add(Y90(qubit))
    XY_to_equator.add(X(qubit))
    XY_to_equator.add(Measure(qubit))
    XY_to_equator.add(Reset(qubit))
    #12
    XY_to_equator.add(X(qubit))
    XY_to_equator.add(Y90(qubit))
    XY_to_equator.add(Measure(qubit))
    XY_to_equator.add(Reset(qubit))
    #13
    XY_to_equator.add(Y(qubit))
    XY_to_equator.add(X90(qubit))
    XY_to_equator.add(Measure(qubit))
    XY_to_equator.add(Reset(qubit))
    #14
    XY_to_equator.add(X90(qubit))
    XY_to_equator.add(X(qubit))
    XY_to_equator.add(Measure(qubit))
    XY_to_equator.add(Reset(qubit))
    #15
    XY_to_equator.add(X(qubit))
    XY_to_equator.add(X90(qubit))
    XY_to_equator.add(Measure(qubit))
    XY_to_equator.add(Reset(qubit))
    #16
    XY_to_equator.add(Y90(qubit))
    XY_to_equator.add(Y(qubit))
    XY_to_equator.add(Measure(qubit))
    XY_to_equator.add(Reset(qubit))
    #17
    XY_to_equator.add(Y(qubit))
    XY_to_equator.add(Y90(qubit))
    XY_to_equator.add(Measure(qubit))
    XY_to_equator.add(Reset(qubit))
    return XY_to_equator

def return_to_excited(qubit: str) -> Schedule:
    XY_to_excited = Schedule("all_XY")
    #18
    XY_to_excited.add(X(qubit))
    XY_to_excited.add(IdlePulse(28e-9))
    XY_to_excited.add(Measure(qubit))
    XY_to_excited.add(Reset(qubit))
    #19
    XY_to_excited.add(Y(qubit))
    XY_to_excited.add(IdlePulse(28e-9))
    XY_to_excited.add(Measure(qubit))
    XY_to_excited.add(Reset(qubit))
    #20
    XY_to_excited.add(X90(qubit))
    XY_to_excited.add(X90(qubit))
    XY_to_excited.add(Measure(qubit))
    XY_to_excited.add(Reset(qubit))
    #21
    XY_to_excited.add(Y90(qubit))
    XY_to_excited.add(Y90(qubit))
    XY_to_excited.add(Measure(qubit))
    XY_to_excited.add(Reset(qubit))

    return XY_to_excited


class All_XY(Measurement):

    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

    def schedule_function(self, repetitions: int = 1024,) -> Schedule:
        """

        Returns
        -------
        :
            An experiment schedule.
        """
        schedule_title = 'multiplexed_all_XY'
        schedule = Schedule(schedule_title, repetitions)

        qubits = self.transmons.keys()

        for this_qubit in qubits:

            schedule.add(return_to_ground(this_qubit))
            schedule.add(return_to_equator(this_qubit))
            schedule.add(return_to_excited(this_qubit))

        return schedule
