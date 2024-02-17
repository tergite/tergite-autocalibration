from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X, CZ
from quantify_scheduler.operations.pulse_library import SetClockFrequency,NumericalPulse,SoftSquarePulse,SquarePulse
from quantify_scheduler.resources import ClockResource
from tergite_acl.calibration_schedules.measurement_base import Measurement
from tergite_acl.utilities.extended_transmon_element import Measure_RO2, Measure_RO1
# from utilities.QPU_connections_visualization import edge_group

import numpy as np

class CZ_chevron(Measurement):

    def __init__(self,transmons,couplers,qubit_state:int=0):
        super().__init__(transmons, couplers=couplers)
        self.qubit_state = qubit_state
        self.couplers = couplers
        self.static_kwargs = {
            'couplers': self.couplers,
            'coupler_pulse_amplitudes': self.attributes_dictionary('coupler_spec_amp'),
            #'cz_pulse_width': self.attributes_dictionary('cz_pulse_width'),
        }

    def schedule_function(
            self,
            couplers: list[str],
            coupler_pulse_amplitudes: dict[str,float],
            cz_pulse_frequencies: dict[str,np.ndarray],
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
        all_qubits = [q for bus in couplers for q in bus.split('_')]
        all_qubits = set(all_qubits) # remove duplicates

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*all_qubits), label="Reset")

        # The outer for loop iterates over all couplers:
        for coupler in couplers:
            qubits = coupler.split(sep='_')
            control_qubit = qubits[0]
            target_qubit = qubits[1]
            cz_clock = f'{coupler}.cz'
            cz_pulse_port = f'{coupler}:fl'
            cz_frequency_values = cz_pulse_frequencies[coupler]
            cz_duration_values = cz_pulse_durations[coupler]
            number_of_durations = len(cz_duration_values)
            cz_amplitude = coupler_pulse_amplitudes[coupler]
            print(f'{ cz_amplitude = }')

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt='end'
            ) #To enforce parallelism we refer to the root relaxation

            schedule.add_resource(
                ClockResource(name=cz_clock,freq= - cz_frequency_values[0] + 4.4e9)
            )

            # The intermidiate loop, iterates over all cz_frequencies
            for freq_index, cz_frequency in enumerate(cz_frequency_values):
                schedule.add(
                    SetClockFrequency(clock=cz_clock, clock_freq_new= - cz_frequency + 4.4e9),
                )

                #The inner for loop iterates over cz pulse durations
                for acq_index, cz_duration in enumerate(cz_duration_values):
                    this_index = freq_index * number_of_durations + acq_index

                    relaxation = schedule.add(Reset(*qubits))

                    for this_qubit in qubits:
                        schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')

                    cz = schedule.add(
                            SoftSquarePulse(
                                duration=cz_duration,
                                amp = cz_amplitude,
                                port=cz_pulse_port,
                                clock=cz_clock,
                            ),
                        )

                    schedule.add(
                        Measure(control_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                        ref_op=cz,rel_time=12e-9, ref_pt="end",
                    )
                    schedule.add(
                        Measure_RO1(target_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                        ref_op=cz,rel_time=12e-9, ref_pt="end",
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
