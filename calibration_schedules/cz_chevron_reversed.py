"""
Module containing a schedule class for Ramsey calibration. (1D parameter sweep, for 2D see ramsey_detunings.py)
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X, CZ
from quantify_scheduler.operations.pulse_library import DRAGPulse,SetClockFrequency,NumericalPulse,SoftSquarePulse,SquarePulse
from quantify_scheduler.resources import ClockResource
from calibration_schedules.measurement_base import Measurement
from utilities.extended_transmon_element import Measure_RO1
from utilities.QPU_connections_visualization import edge_group
from matplotlib import pyplot as plt

import numpy as np

class CZ_chevron(Measurement):

    def __init__(self,transmons,couplers,qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.couplers = couplers
        self.static_kwargs = {
            'qubits': self.qubits,
            'mw_frequencies': self.attributes_dictionary('f01'),
            'mw_pulse_durations': self.attributes_dictionary('duration'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
            'mw_ef_amps180': self.attributes_dictionary('ef_amp180'),
            'mw_frequencies_12': self.attributes_dictionary('f12'),
            #TODO temporarily comment out as they are hardcoded in the schedule
            #'cz_pulse_duration': self.attributes_dictionary('cz_pulse_duration'),
            #'cz_pulse_width': self.attributes_dictionary('cz_pulse_width'),
        }

    def schedule_function(
            self,
            qubits: list[str],
            coupler: str,
            cz_pulse_frequencies_sweep: dict[str,np.ndarray],
            cz_pulse_durations: dict[str,np.ndarray],
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
        schedule = Schedule("CZ_chevron",repetitions)

        cz_frequency_values = np.array(list(cz_pulse_frequencies_sweep.values())[0])
        cz_duration_values = list(cz_pulse_durations.values())[0]

        schedule.add_resource(
            ClockResource(name=coupler+'.cz',freq=cz_frequency_values[0])
        )

        number_of_durations = len(cz_duration_values)

        # The outer loop, iterates over all cz_frequencies
        for freq_index, cz_frequency in enumerate(cz_frequency_values):
            cz_clock = f'{coupler}.cz'
            cz_pulse_port = f'{coupler}:fl'
            schedule.add(
                SetClockFrequency(clock=cz_clock, clock_freq_new=cz_frequency),
            )

            #The inner for loop iterates over cz pulse durations
            for acq_index, cz_duration in enumerate(cz_duration_values):

                relaxation = schedule.add(Reset(*qubits))

                for this_qubit in qubits:
                    schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')

                cz_amplitude = 0.2
                cz = schedule.add(
                        SquarePulse(
                            duration=cz_duration,
                            amp = cz_amplitude,
                            port=cz_pulse_port,
                            clock=cz_clock,
                        ),
                        ref_pt='end',
                    )

                for this_qubit in qubits:
                    this_index = freq_index * number_of_durations + acq_index
                    schedule.add(
                        Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                        ref_op=cz,rel_time=40e-9, ref_pt="end",
                    )
        return schedule

        # Add calibration points
        # relaxation_calib = schedule.add(Reset(*qubits), label=f"Reset_Calib")
        # for this_qubit in qubits:
        #     i = this_index
        #     schedule.add(Reset(this_qubit))
        #     schedule.add(
        #         Measure(
        #             this_qubit,
        #             acq_index=i+1
        #         ),
        #         label=f"Calibration point |0> {this_qubit}",ref_op=relaxation_calib,ref_pt='end',
        #     )

        #     schedule.add(Reset(this_qubit))
        #     schedule.add(X(this_qubit))
        #     schedule.add(
        #         Measure(
        #             this_qubit,
        #             acq_index=i+2
        #         ),
        #         label=f"Calibration point |1> {this_qubit}",
        #     )
        #     f12_clock = f'{this_qubit}.12'
        #     schedule.add(Reset(this_qubit))
        #     schedule.add(X(this_qubit))
        #     f12_amp = mw_ef_amps180[this_qubit]
        #     schedule.add(
        #         DRAGPulse(
        #             duration=mw_pulse_durations[this_qubit],
        #             G_amp=f12_amp,
        #             D_amp=0,
        #             port=mw_pulse_ports[this_qubit],
        #             clock=f12_clock,
        #             phase=0,
        #         ),
        #     )
        #     schedule.add(
        #         Measure(
        #             this_qubit,
        #             acq_index=i+3
        #         ),
        #         label=f"Calibration point |2> {this_qubit}",
        #     )
        #return schedule
