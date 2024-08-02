import numpy as np
from quantify_scheduler import Schedule
from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.extended_coupler_edge import CompositeSquareEdge
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon
from quantify_scheduler.operations.pulse_library import IdlePulse
from quantify_scheduler.operations.pulse_library import (
    SetClockFrequency,
    SoftSquarePulse,
    ResetClockPhase,
)
from quantify_scheduler.resources import ClockResource
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from quantify_scheduler.enums import BinMode


class CZ_Parametrisation_Fix_Duration(BaseMeasurement):
    def __init__(
        self,
        transmons: dict[str, ExtendedTransmon],
        couplers: dict[str, CompositeSquareEdge],
        qubit_state: int = 0,
    ):
        super().__init__(transmons)
        self.transmons = transmons
        self.qubit_state = qubit_state
        self.couplers = couplers

    def schedule_function(
        self,
        cz_parking_currents: dict[str, np.ndarray],
        cz_pulse_frequencies: dict[str, np.ndarray],
        cz_pulse_amplitudes: dict[str, np.ndarray],
        cz_pulse_duration: float = 240e-9,
        repetitions: int = 1024,
    ) -> Schedule:
        """
        Generate a schedule for performing a Ramsey fringe measurement on multiple qubits.
        Can be used both to finetune the qubit frequency and to measure the qubit dephasing time T_2. (1D parameter sweep)

        Schedule sequence
            Reset -> pi/2-pulse -> Idle(tau) -> pi/2-pulse -> Measure

        Parameters
        ----------
        self
            Contains all qubit states.
        qubits
            A list of two qubits to perform the experiment on. i.e. [['q1','q2'],['q3','q4'],...]
        mw_clocks_12
            Clocks for the 12 transition frequency of the qubits.
        mw_ef_amps180
            Amplitudes used for the excitation of the qubits to calibrate for the 12 transition.
        mw_frequencies_12
            Frequencies used for the excitation of the qubits to calibrate for the 12 transition.
        mw_pulse_ports
            Location on the device where the pulsed used for excitation of the qubits to calibrate for the 12 transition is located.
        mw_pulse_durations
            Pulse durations used for the excitation of the qubits to calibrate for the 12 transition.
        cz_pulse_frequency
            The frequency of the CZ pulse.
        cz_pulse_amplitude
            The amplitude of the CZ pulse.
        cz_pulse_duration
            The duration of the CZ pulse.
        cz_pulse_width
            The width of the CZ pulse.
        testing_group
            The edge group to be tested. 0 means all edges.
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """
        schedule = Schedule("CZ_Frequency_And_Amplitude", repetitions)

        cz_parking_currents_values = list(cz_pulse_amplitudes.values())[0]
        cz_frequency_values = np.array(list(cz_pulse_frequencies.values())[0])
        cz_amplitude_values = list(cz_pulse_amplitudes.values())[0]

        for cz_current in cz_parking_currents_values:
            self.redis_field = cz_current
            schedule = self.loop_frequencies_and_aplitudes(
                schedule, cz_amplitude_values, cz_frequency_values, cz_pulse_duration
            )

        return schedule


def loop_frequencies_and_aplitudes(
    self, schedule, cz_amplitude_values, cz_frequency_values, cz_pulse_duration
) -> Schedule:
    coupler = list(self.couplers.keys())[0]
    all_couplers = [coupler]

    for this_coupler in all_couplers:
        if this_coupler in ["q21_q22", "q22_q23", "q23_q24", "q24_q25"]:
            downconvert = 0
        else:
            downconvert = 4.4e9
        schedule.add_resource(
            ClockResource(
                name=coupler + ".cz", freq=-cz_frequency_values[0] + downconvert
            )
        )

    # The outer loop, iterates over all cz_frequencies
    for freq_index, cz_frequency in enumerate(cz_frequency_values):
        cz_clock = f"{coupler}.cz"
        schedule.add(
            SetClockFrequency(
                clock=cz_clock, clock_freq_new=-cz_frequency + downconvert
            ),
        )
        schedule = loop_amplitudes(
            coupler, schedule, cz_amplitude_values, freq_index, cz_pulse_duration
        )

    return schedule


def loop_amplitudes(
    self, schedule, coupler, cz_amplitude_values, freq_index, cz_pulse_duration
) -> Schedule:
    # The inner for loop iterates over cz pulse amplitude
    number_of_amplitudess = len(cz_amplitude_values)
    qubits = coupler.split(sep="_")
    for acq_index, cz_amplitude in enumerate(cz_amplitude_values):
        this_index = freq_index * number_of_amplitudess + acq_index

        relaxation = schedule.add(Reset(*qubits))

        for this_qubit in qubits:
            schedule.add(X(this_qubit), ref_op=relaxation, ref_pt="end")

        buffer = schedule.add(IdlePulse(4e-9))

        schedule.add(ResetClockPhase(clock=coupler + ".cz"))
        cz_clock = f"{coupler}.cz"
        cz_pulse_port = f"{coupler}:fl"

        cz = schedule.add(
            SoftSquarePulse(
                duration=cz_pulse_duration,
                amp=cz_amplitude,
                port=cz_pulse_port,
                clock=cz_clock,
            ),
        )
        buffer = schedule.add(IdlePulse(4e-9))

        for this_qubit in qubits:
            schedule.add(
                Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                ref_op=buffer,
                rel_time=4e-9,
                ref_pt="end",
            )

    return schedule
