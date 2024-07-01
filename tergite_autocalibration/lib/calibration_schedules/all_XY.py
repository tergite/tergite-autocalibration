from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import X, Measure, Reset, Rxy
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon
from tergite_autocalibration.lib.base.measurement import BaseMeasurement
import numpy as np

all_XY_angles = {
    0: ({"theta": 0, "phi": 0}, {"theta": 0, "phi": 0}),
    1: ({"theta": 180, "phi": 0}, {"theta": 180, "phi": 0}),
    2: ({"theta": 180, "phi": 90}, {"theta": 180, "phi": 90}),
    3: ({"theta": 180, "phi": 0}, {"theta": 180, "phi": 90}),
    4: ({"theta": 180, "phi": 90}, {"theta": 180, "phi": 0}),
    5: ({"theta": 90, "phi": 0}, {"theta": 0, "phi": 0}),
    6: ({"theta": 90, "phi": 90}, {"theta": 0, "phi": 0}),
    7: ({"theta": 90, "phi": 0}, {"theta": 90, "phi": 90}),
    8: ({"theta": 90, "phi": 90}, {"theta": 90, "phi": 0}),
    9: ({"theta": 90, "phi": 0}, {"theta": 180, "phi": 90}),
    10: ({"theta": 90, "phi": 90}, {"theta": 180, "phi": 0}),
    11: ({"theta": 180, "phi": 0}, {"theta": 90, "phi": 90}),
    12: ({"theta": 180, "phi": 90}, {"theta": 90, "phi": 0}),
    13: ({"theta": 90, "phi": 0}, {"theta": 180, "phi": 0}),
    14: ({"theta": 180, "phi": 0}, {"theta": 90, "phi": 0}),
    15: ({"theta": 90, "phi": 90}, {"theta": 180, "phi": 90}),
    16: ({"theta": 180, "phi": 90}, {"theta": 90, "phi": 90}),
    17: ({"theta": 180, "phi": 0}, {"theta": 0, "phi": 0}),
    18: ({"theta": 180, "phi": 90}, {"theta": 0, "phi": 0}),
    19: ({"theta": 90, "phi": 0}, {"theta": 90, "phi": 0}),
    20: ({"theta": 90, "phi": 90}, {"theta": 90, "phi": 90}),
}


class All_XY(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

    def schedule_function(
        self,
        XY_index: dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:
        """

        Returns
        -------
        :
            An experiment schedule.
        """
        schedule_title = "multiplexed_all_XY"
        schedule = Schedule(schedule_title, repetitions)

        qubits = self.transmons.keys()

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        for this_qubit in qubits:
            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt="end"
            )  # To enforce parallelism we refer to the root relaxation

            for acq_index, pulses in all_XY_angles.items():
                first_theta = pulses[0]["theta"]
                first_phi = pulses[0]["phi"]
                schedule.add(Rxy(qubit=this_qubit, theta=first_theta, phi=first_phi))
                second_theta = pulses[1]["theta"]
                second_phi = pulses[1]["phi"]
                schedule.add(Rxy(qubit=this_qubit, theta=second_theta, phi=second_phi))
                schedule.add(Measure(this_qubit, acq_index=acq_index))
                schedule.add(Reset(this_qubit))

            # 0 calibration point
            schedule.add(Reset(this_qubit))
            schedule.add(Reset(this_qubit))
            schedule.add(Measure(this_qubit, acq_index=acq_index + 1))
            schedule.add(Reset(this_qubit))

            # 1 calibration point
            schedule.add(Reset(this_qubit))
            schedule.add(Reset(this_qubit))
            schedule.add(X(this_qubit))
            schedule.add(Measure(this_qubit, acq_index=acq_index + 2))
            schedule.add(Reset(this_qubit))

        return schedule
