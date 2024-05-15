"""
Module containing a schedule class for Ramsey calibration. (1D parameter sweep, for 2D see ramsey_detunings.py)
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X, CZ
from quantify_scheduler.operations.pulse_library import GaussPulse,SuddenNetZeroPulse,ResetClockPhase,IdlePulse,DRAGPulse,SetClockFrequency,NumericalPulse,SoftSquarePulse,SquarePulse
from quantify_scheduler.operations.pulse_library import RampPulse,DRAGPulse,SetClockFrequency,NumericalPulse,SoftSquarePulse,SquarePulse, ResetClockPhase
from quantify_scheduler.resources import ClockResource
from tergite_acl.lib.measurement_base import Measurement
from tergite_acl.utils.extended_transmon_element import Measure_RO1, Rxy_12
from tergite_acl.config.coupler_config import edge_group, qubit_types
from matplotlib import pyplot as plt
from tergite_acl.utils.extended_coupler_edge import CompositeSquareEdge
from tergite_acl.utils.extended_transmon_element import ExtendedTransmon

import numpy as np
import redis

class Reset_chevron_dc(Measurement):
    # for testing dc reset

    def __init__(self,transmons,coupler,qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.coupler = coupler
        self.static_kwargs = {
            'coupler': self.coupler,
            # 'mw_frequencies': self.attributes_dictionary('f01'),
            # 'mw_pulse_durations': self.attributes_dictionary('duration'),
            # 'mw_pulse_ports': self.attributes_dictionary('microwave'),
            # 'mw_ef_amps180': self.attributes_dictionary('ef_amp180'),
            # 'mw_frequencies_12': self.attributes_dictionary('f12'),
            #TODO temporarily comment out as they are hardcoded in the schedule
            #'cz_pulse_duration': self.attributes_dictionary('cz_pulse_duration'),
            #'cz_pulse_width': self.attributes_dictionary('cz_pulse_width'),
        }

    def schedule_function(
            self,
            coupler: str,
            # cz_pulse_frequencies_sweep: dict[str,np.ndarray],
            cz_pulse_amplitudes: dict[str,np.ndarray],
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
        schedule = Schedule("reset_chevron",repetitions)
        qubits = coupler.split(sep='_')

        # cz_frequency_values = np.array(list(cz_pulse_frequencies_sweep.values())[0])
        reset_duration_values = list(cz_pulse_durations.values())[0]
        reset_pulse_amplitude_values = list(cz_pulse_amplitudes.values())[0]
        print(f'{ reset_duration_values = }')
        print(f'{ reset_pulse_amplitude_values = }')

        # print(f'{ cz_frequency_values[0] = }')

        # schedule.add_resource(
        #     ClockResource(name=coupler+'.cz',freq= - cz_frequency_values[0] + 4.4e9)
        # )

        # schedule.add_resource(
        #     ClockResource(name=coupler+'.cz',freq= 4.4e9)
        # )

        schedule.add_resource(
            ClockResource(name=coupler+'.cz',freq= 0e9)
        )

        number_of_durations = len(reset_duration_values)

        # The outer loop, iterates over all cz_frequencies
        for freq_index, reset_amplitude in enumerate(reset_pulse_amplitude_values):
            cz_clock = f'{coupler}.cz'
            cz_pulse_port = f'{coupler}:fl'
            # schedule.add(
            #     SetClockFrequency(clock=cz_clock, clock_freq_new= - cz_frequency + 4.4e9),
            # )
            # schedule.add(
            #     SetClockFrequency(clock=cz_clock, clock_freq_new=4.4e9),
            # )

            #The inner for loop iterates over cz pulse durations
            for acq_index, reset_duration in enumerate(reset_duration_values):
                this_index = freq_index * number_of_durations + acq_index

                relaxation = schedule.add(Reset(*qubits))

                for this_qubit in qubits:
                    # schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                    if qubit_types[this_qubit] == 'Target':
                        # schedule.add(IdlePulse(32e-9), ref_op=relaxation, ref_pt='end')
                        # schedule.add(IdlePulse(20e-9))
                        schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                        schedule.add(Rxy_12(this_qubit))
                    else:
                        schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                        # schedule.add(Rxy_12(this_qubit))
                        # schedule.add(IdlePulse(20e-9))
                        # schedule.add(IdlePulse(32e-9), ref_op=relaxation, ref_pt='end')


                schedule.add(ResetClockPhase(clock=coupler+'.cz'))
                
                buffer = schedule.add(IdlePulse(4e-9))

                reset_duration_qc = 564e-09
                reset_amplitude_qc = 8e-2

                reset_duration_cr = 904e-09
                reset_amplitude_cr = -8.75e-2

                reset_duration_cr_fg = 901e-09
                reset_amplitude_cr_fg = -0.15526

                reset_duration_qc_fg = 16e-09
                reset_amplitude_qc_fg = 0.1155

                reset_duration_wait = 2000e-09
                
                # repetition test

                # for i in range(int(reset_duration)):
                #     qc = schedule.add(                
                #                 RampPulse(
                #                     duration = reset_duration_qc,
                #                     offset = reset_amplitude_qc,
                #                     amp = - reset_amplitude_qc,
                #                     port = cz_pulse_port,
                #                     clock = cz_clock,
                #                 ),
                #             )

                #     buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc * 1e9 / 4) * 4e-9)
                #     # # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
                
                #     cr = schedule.add(
                #                 RampPulse(
                #                     duration = reset_duration_cr,
                #                     # duration = 1000e-09,
                #                     # offset = reset_amplitude_cr,
                #                     # amp = -reset_amplitude_cr,
                #                     # duration = reset_duration,
                #                     offset = reset_amplitude,
                #                     # amp = -reset_amplitude,
                #                     amp = 0,
                #                     port = cz_pulse_port,
                #                     clock = cz_clock,
                #                 ),
                #             )

                #     buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr * 1e9 / 4) * 4e-9)
                
                # step 3 - calibrate fg reset qc pulse
                # qc = schedule.add(
                #             RampPulse(
                #                 # duration = reset_duration_qc_fg,
                #                 # offset = reset_amplitude_qc_fg,
                #                 offset = reset_amplitude,
                #                 duration = reset_duration,
                #                 amp = reset_amplitude,
                #                 # amp = 0,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc_fg * 1e9 / 4) * 4e-9)
                
                # cr = schedule.add(
                #             RampPulse(
                #                 duration = reset_duration_cr,
                #                 offset = reset_amplitude_cr,
                #                 amp = -reset_amplitude_cr/11,
                #                 # duration = reset_duration,
                #                 # offset = reset_amplitude,
                #                 # amp = -reset_amplitude/11,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr * 1e9 / 4) * 4e-9)
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
                # buffer = schedule.add(IdlePulse(np.ceil( reset_duration * 1e9 / 4) * 4e-9),ref_op=buffer, ref_pt='end')
                # buffer = schedule.add(IdlePulse(np.ceil( reset_duration_wait * 1e9 / 4) * 4e-9),ref_op=buffer, ref_pt='end')

                # qc = schedule.add(
                #             RampPulse(
                #                 offset = reset_amplitude,
                #                 duration = reset_duration,
                #                 # amp = reset_amplitude,
                #                 amp = 0.,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
                
                # qc = schedule.add(
                #             RampPulse(
                #                 # offset = reset_amplitude/1.5,
                #                 # duration = reset_duration,
                #                 # amp = reset_amplitude,
                #                 duration = reset_duration_qc,
                #                 offset = reset_amplitude_qc/1.5,
                #                 amp = reset_amplitude_qc,
                #                 # amp = 0,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc * 1e9 / 4) * 4e-9)
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
            
                # cr = schedule.add(
                #             RampPulse(
                #                 duration = reset_duration_cr,
                #                 offset = reset_amplitude_cr,
                #                 amp = -reset_amplitude_cr/11,
                #                 # duration = reset_duration,
                #                 # offset = reset_amplitude,
                #                 # amp = -reset_amplitude/11,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr * 1e9 / 4) * 4e-9)
                
                # buffer = schedule.add(IdlePulse(np.ceil( reset_duration_wait * 1e9 / 4) * 4e-9),ref_op=buffer, ref_pt='end')

                # step 1 - calibrate ge/f reset qc pulse
                # qc = schedule.add(
                #             RampPulse(
                #                 offset = reset_amplitude,
                #                 duration = reset_duration,
                #                 amp = 0,
                #                 # amp = 0.,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
                
                buffer = schedule.add(IdlePulse(4e-9))
                for this_qubit in qubits:
                    # schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                    if qubit_types[this_qubit] == 'Target':
                        # schedule.add(IdlePulse(32e-9), ref_op=buffer, ref_pt='end')
                        # schedule.add(IdlePulse(20e-9))
                        # schedule.add(X(this_qubit))
                        schedule.add(Rxy_12(this_qubit,theta = 90), ref_op=buffer, ref_pt='end')
                    else:
                        # schedule.add(Rxy_12(this_qubit,theta = 90), ref_op=buffer, ref_pt='end')
                        # schedule.add(X(this_qubit), ref_op=buffer, ref_pt='end')
                        # schedule.add(Rxy_12(this_qubit))
                        # schedule.add(IdlePulse(20e-9))
                        schedule.add(IdlePulse(32e-9), ref_op=buffer, ref_pt='end')
                
                buffer = schedule.add(IdlePulse(4e-9))
                
                # def tan_pulse(int_duration=10,amp=-0.5, int_window=1/50, tail=1):
                #     if amp < 0:
                #         int_window = -int_window
                #     tlist_int = np.arange(0,int_duration,1)
                #     tan = int_window*np.tan((tlist_int/(int_duration+tail)-0.5)*np.pi)+amp
                #     if int_window<0:
                #         tan[tan>0] = 0
                #     else:
                #         tan[tan<0] = 0
                #     return tan

                # t = np.arange(0,reset_duration*1e9,1)*1e-9
                
                # qc = schedule.add(
                #     NumericalPulse(
                #         samples=tan_pulse(int_duration=reset_duration*1e9,amp=reset_amplitude, int_window=1/1000, tail=1),  # Numerical pulses can be complex as well.
                #         t_samples=t,
                #         port=cz_pulse_port,
                #         clock=cz_clock,
                #     ),
                # )
                # reset_duration_set = 600e-09
                # qc = schedule.add(
                #             RampPulse(
                #                 duration = reset_duration,
                #                 # offset = reset_amplitude,
                #                 offset = reset_amplitude/1.5,
                #                 amp = reset_amplitude,
                #                 # amp = 0,
                #                 # amp = -reset_amplitude,
                #                 # offset = reset_amplitude,
                #                 # duration = reset_duration_qc,
                #                 # offset = reset_amplitude_qc/1.5,
                #                 # amp = reset_amplitude_qc,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc * 1e9 / 4) * 4e-9)
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
            
                # step 2 - calibrate ge/f reset cr pulse

                # for this_qubit in qubits:
                #     # schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                #     if qubit_types[this_qubit] == 'Target':
                #         schedule.add(IdlePulse(20e-9), ref_op=buffer, ref_pt='end')
                #         # schedule.add(IdlePulse(20e-9))
                #         # schedule.add(X(this_qubit), ref_op=buffer, ref_pt='end')
                #         # schedule.add(Rxy_12(this_qubit,theta = 90))
                #     else:
                #         schedule.add(X(this_qubit), ref_op=buffer, ref_pt='end')
                #         # schedule.add(Rxy_12(this_qubit))
                #         # schedule.add(IdlePulse(20e-9))
                #         # schedule.add(IdlePulse(20e-9), ref_op=buffer, ref_pt='end')

                # buffer = schedule.add(IdlePulse(4e-9))
                
                # cr = schedule.add(
                #             RampPulse(
                #                 # duration = reset_duration_cr,
                #                 # offset = reset_amplitude_cr,
                #                 # amp = -reset_amplitude_cr/11,
                #                 duration = reset_duration,
                #                 offset = reset_amplitude,
                #                 amp = -reset_amplitude/11,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr * 1e9 / 4) * 4e-9)
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
                # # buffer = schedule.add(IdlePulse(np.ceil( reset_duration_wait * 1e9 / 4) * 4e-9),ref_op=buffer, ref_pt='end')
                
                qc = schedule.add(
                            RampPulse(
                                # offset = reset_amplitude/1.5,
                                # duration = reset_duration,
                                # amp = reset_amplitude,
                                duration = reset_duration_qc,
                                offset = reset_amplitude_qc/1.5,
                                amp = reset_amplitude_qc,
                                # amp = 0,
                                port = cz_pulse_port,
                                clock = cz_clock,
                            ),
                        )

                buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc * 1e9 / 4) * 4e-9)
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
            
                cr = schedule.add(
                            RampPulse(
                                # duration = reset_duration_cr,
                                # offset = reset_amplitude_cr,
                                # amp = -reset_amplitude_cr/11,
                                duration = reset_duration,
                                offset = reset_amplitude,
                                amp = -reset_amplitude/11,
                                port = cz_pulse_port,
                                clock = cz_clock,
                            ),
                        )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr * 1e9 / 4) * 4e-9)
                buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
                # buffer = schedule.add(IdlePulse(np.ceil( reset_duration_wait * 1e9 / 4) * 4e-9),ref_op=buffer, ref_pt='end')
                
                qc = schedule.add(
                            RampPulse(
                                # offset = reset_amplitude,
                                # duration = reset_duration,
                                # amp = 0,
                                # amp = reset_amplitude,
                                duration = reset_duration_qc,
                                offset = reset_amplitude_qc/1.5,
                                amp = reset_amplitude_qc,
                                port = cz_pulse_port,
                                clock = cz_clock,
                            ),
                        )

                buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc * 1e9 / 4) * 4e-9)
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
            
                # cr = schedule.add(
                #             RampPulse(
                #                 duration = reset_duration_cr,
                #                 offset = reset_amplitude_cr,
                #                 amp = -reset_amplitude_cr/11,
                #                 # duration = reset_duration,
                #                 # offset = reset_amplitude,
                #                 # amp = -reset_amplitude/11,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr * 1e9 / 4) * 4e-9)
                
                # for this_qubit in qubits:
                #     # schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                #     if qubit_types[this_qubit] == 'Target':
                #         # schedule.add(IdlePulse(20e-9), ref_op=buffer, ref_pt='end')
                #         # schedule.add(IdlePulse(20e-9))
                #         schedule.add(X(this_qubit), ref_op=buffer, ref_pt='end')
                #         # schedule.add(Rxy_12(this_qubit), ref_op=buffer, ref_pt='end')
                #     else:
                #         # schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                #         # schedule.add(Rxy_12(this_qubit))
                #         # schedule.add(IdlePulse(20e-9))
                #         schedule.add(IdlePulse(20e-9), ref_op=buffer, ref_pt='end')

                # qc = schedule.add(
                #             RampPulse(
                #                 # offset = reset_amplitude/1.5,
                #                 # duration = reset_duration,
                #                 # amp = reset_amplitude,
                #                 duration = reset_duration_qc,
                #                 offset = reset_amplitude_qc/1.5,
                #                 amp = reset_amplitude_qc,
                #                 # amp = 0,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc * 1e9 / 4) * 4e-9)
                # # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)

          
                # # step 4 - check fg reset cr pulse
                
                # qc = schedule.add(
                #             RampPulse(
                #                 duration = reset_duration_qc_fg,
                #                 offset = reset_amplitude_qc_fg,
                #                 amp = 0,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc_fg * 1e9 / 4) * 4e-9)
            
                # cr = schedule.add(
                #             RampPulse(
                #                 duration = reset_duration_cr,
                #                 offset = reset_amplitude_cr,
                #                 amp = 0,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr * 1e9 / 4) * 4e-9)

                # cr = schedule.add(
                #             RampPulse(
                #                 duration = reset_duration_cr_gf,
                #                 offset = reset_amplitude_cr_gf,
                #                 amp = 0,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr_gf * 1e9 / 4) * 4e-9)
            
                # qc = schedule.add(
                #             RampPulse(
                #                 duration = reset_duration_qc_fg,
                #                 offset = reset_amplitude_qc_fg,
                #                 amp = - reset_amplitude_qc_fg,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc_fg * 1e9 / 4) * 4e-9)

                # # step 5 - full reset

                # qc = schedule.add(
                #             RampPulse(
                #                 duration = reset_duration_qc,
                #                 offset = reset_amplitude_qc,
                #                 amp = - reset_amplitude_qc,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc * 1e9 / 4) * 4e-9)

                # cr = schedule.add(
                #             RampPulse(
                #                 duration = reset_duration_cr,
                #                 offset = reset_amplitude_cr,
                #                 amp = 0,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr * 1e9 / 4) * 4e-9)

                # qc = schedule.add(
                #             RampPulse(
                #                 duration = reset_duration_qc_fg,
                #                 offset = reset_amplitude_qc_fg,
                #                 amp = 0,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc_fg * 1e9 / 4) * 4e-9)

                # cr = schedule.add(
                #             RampPulse(
                #                 duration = reset_duration_cr,
                #                 offset = reset_amplitude_cr,
                #                 amp = 0,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr * 1e9 / 4) * 4e-9)


        ###################################################################

                buffer_end = schedule.add(IdlePulse(4e-9))
                
                for this_qubit in qubits:
                    schedule.add(
                        Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                        ref_op=buffer_end,rel_time=20e-9, ref_pt="end",
                    )
        return schedule

class Reset_chevron_ac(Measurement):
    # for testing reset

    def __init__(self,transmons,coupler,qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.coupler = coupler
        self.static_kwargs = {
            'coupler': self.coupler,
            # 'mw_frequencies': self.attributes_dictionary('f01'),
            # 'mw_pulse_durations': self.attributes_dictionary('duration'),
            # 'mw_pulse_ports': self.attributes_dictionary('microwave'),
            # 'mw_ef_amps180': self.attributes_dictionary('ef_amp180'),
            # 'mw_frequencies_12': self.attributes_dictionary('f12'),
            #TODO temporarily comment out as they are hardcoded in the schedule
            #'cz_pulse_duration': self.attributes_dictionary('cz_pulse_duration'),
            #'cz_pulse_width': self.attributes_dictionary('cz_pulse_width'),
        }

    def schedule_function(
            self,
            coupler: str,
            cz_pulse_frequencies_sweep: dict[str,np.ndarray],
            cz_pulse_durations: dict[str,np.ndarray],
            cz_pulse_amplitude: float = 0.5,
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
        qubits = coupler.split(sep='_')

        cz_frequency_values = np.array(list(cz_pulse_frequencies_sweep.values())[0])
        cz_duration_values = list(cz_pulse_durations.values())[0]

        # print(f'{ cz_frequency_values[0] = }')
        couplers_list = [coupler]
        # find cz parameters from redis
        redis_connection = redis.Redis(decode_responses=True)
        cz_pulse_amplitude = {}
        for this_coupler in couplers_list:
            qubits = this_coupler.split(sep='_')
            cz_amplitude_values = []
            for qubit in qubits: 
                redis_config = redis_connection.hgetall(f"transmons:{qubit}")
                cz_amplitude_values.append(float(redis_config['cz_pulse_amplitude']))
            cz_pulse_amplitude[this_coupler] = cz_amplitude_values[0]
        print(f'{cz_pulse_amplitude = }')

        schedule.add_resource(
            ClockResource(name=coupler+'.cz',freq= - cz_frequency_values[0] + 4.4e9)
        )

        number_of_durations = len(cz_duration_values)

        # The outer loop, iterates over all cz_frequencies
        for freq_index, cz_frequency in enumerate(cz_frequency_values):
            cz_clock = f'{coupler}.cz'
            cz_pulse_port = f'{coupler}:fl'
            schedule.add(
                SetClockFrequency(clock=cz_clock, clock_freq_new= - cz_frequency + 4.4e9),
            )
            # schedule.add(
            #     SetClockFrequency(clock=cz_clock, clock_freq_new=4.4e9),
            # )

            #The inner for loop iterates over cz pulse durations
            for acq_index, cz_duration in enumerate(cz_duration_values):
                this_index = freq_index * number_of_durations + acq_index

                relaxation = schedule.add(Reset(*qubits))

                for this_qubit in qubits:
                    # schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                    if this_qubit == 'q15':
                        schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                        schedule.add(Rxy_12(this_qubit))
                    else:
                        schedule.add(IdlePulse(40e-9))
                        # schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                        # schedule.add(Rxy_12(this_qubit))

                # cz_amplitude = 0.5
                buffer = schedule.add(IdlePulse(12e-9))

                cz = schedule.add(
                        SoftSquarePulse(
                            duration=cz_duration,
                            amp = cz_pulse_amplitude[this_coupler],
                            port=cz_pulse_port,
                            clock=cz_clock,
                        ),
                    )
                
                # reset test
                buffer = schedule.add(IdlePulse(cz_duration_values[-1]-cz_duration))
                # if this_qubit == 'q15':
                    # schedule.add(X90(this_qubit), ref_op=buffer, ref_pt='end')
                    # schedule.add(Rxy_12(this_qubit))
                # else:
                #     schedule.add(IdlePulse(20e-9))

                buffer = schedule.add(IdlePulse(12e-9))

                for this_qubit in qubits:
                    schedule.add(
                        Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                        ref_op=cz,rel_time=12e-9, ref_pt="end",
                    )
        return schedule

class CZ_chevron(Measurement):

    def __init__(self, transmons: dict[str, ExtendedTransmon],couplers: dict[str, CompositeSquareEdge], qubit_state: int = 0):
        super().__init__(transmons)
        self.transmons = transmons
        self.qubit_state = qubit_state
        self.couplers = couplers

    def schedule_function(
            self,
            cz_pulse_frequencies: dict[str,np.ndarray],
            cz_pulse_durations: dict[str,np.ndarray],
            opt_cz_pulse_amplitude: dict[str,float] = None,
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
        coupler = list(self.couplers.keys())[0]
        qubits = coupler.split(sep='_')

        cz_frequency_values = np.array(list(cz_pulse_frequencies.values())[0])
        cz_duration_values = list(cz_pulse_durations.values())[0]

        # print(f'{ cz_frequency_values[0] = }')
        all_couplers = [coupler]
        # find cz parameters from redis
        redis_connection = redis.Redis(decode_responses=True)
        cz_pulse_amplitude = {}
        for this_coupler in all_couplers:
            redis_config = redis_connection.hgetall(f"couplers:{this_coupler}")
            cz_pulse_amplitude[this_coupler] = float(redis_config['cz_pulse_amplitude'])
            
            if this_coupler in ['q14_q19','q17_q22']:
                downconvert = 0
            else:
                downconvert = 4.4e9
            schedule.add_resource(
                ClockResource(name=coupler+'.cz',freq= - cz_frequency_values[0]+downconvert)
            )
        print(f'{opt_cz_pulse_amplitude = }')
        for this_coupler in all_couplers:
            if opt_cz_pulse_amplitude is not None:
                cz_pulse_amplitude[this_coupler] += opt_cz_pulse_amplitude[this_coupler]
        print(f'{cz_pulse_amplitude = }')

        number_of_durations = len(cz_duration_values)

        # The outer loop, iterates over all cz_frequencies
        for freq_index, cz_frequency in enumerate(cz_frequency_values):
            cz_clock = f'{coupler}.cz'
            cz_pulse_port = f'{coupler}:fl'
            schedule.add(
                SetClockFrequency(clock=cz_clock, clock_freq_new= - cz_frequency + downconvert),
            )

            #The inner for loop iterates over cz pulse durations
            for acq_index, cz_duration in enumerate(cz_duration_values):
                this_index = freq_index * number_of_durations + acq_index

                relaxation = schedule.add(Reset(*qubits))

                for this_qubit in qubits:
                    schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')

                # cz_amplitude = 0.5
                buffer = schedule.add(IdlePulse(4e-9))
            
                schedule.add(ResetClockPhase(clock=coupler+'.cz'))

                cz = schedule.add(
                        SoftSquarePulse(
                            duration=cz_duration,
                            amp = cz_pulse_amplitude[this_coupler],
                            port=cz_pulse_port,
                            clock=cz_clock,
                        ),
                    )

                buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( cz_duration * 1e9 / 4) * 4e-9)

                for this_qubit in qubits:
                    schedule.add(
                        Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                        ref_op=buffer,rel_time=4e-9, ref_pt="end",
                    )
        return schedule

class CZ_chevron_duration(Measurement):

    def __init__(self,transmons,coupler,qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.coupler = coupler
        self.static_kwargs = {
            'coupler': self.coupler,
            # 'mw_frequencies': self.attributes_dictionary('f01'),
            # 'mw_pulse_durations': self.attributes_dictionary('duration'),
            # 'mw_pulse_ports': self.attributes_dictionary('microwave'),
            # 'mw_ef_amps180': self.attributes_dictionary('ef_amp180'),
            # 'mw_frequencies_12': self.attributes_dictionary('f12'),
            #TODO temporarily comment out as they are hardcoded in the schedule
            # 'cz_pulse_duration': self.attributes_dictionary('cz_pulse_duration'),
            #'cz_pulse_width': self.attributes_dictionary('cz_pulse_width'),
        }

    def schedule_function(
            self,
            coupler: str,
            cz_pulse_frequencies_sweep: dict[str,np.ndarray],
            cz_pulse_amplitudes: dict[str,np.ndarray],
            # cz_pulse_duration: dict[str,float],
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
        qubits = coupler.split(sep='_')

        # find cz parameters from redis
        redis_connection = redis.Redis(decode_responses=True)
        cz_pulse_duration = {}
        for qubit in qubits: 
            redis_config = redis_connection.hgetall(f"transmons:{qubit}")
            cz_pulse_duration[qubit] = float(redis_config['cz_pulse_duration'])

        cz_frequency_values = np.array(list(cz_pulse_frequencies_sweep.values())[0])
        cz_pulse_amplitude_values = list(cz_pulse_amplitudes.values())[0]
        cz_duration = cz_pulse_duration[qubits[0]]
        print(f'{ cz_duration = }')

        schedule.add_resource(
            ClockResource(name=coupler+'.cz',freq= - cz_frequency_values[0] + 4.4e9)
        )

        number_of_amplitudes = len(cz_pulse_amplitude_values)

        # The outer loop, iterates over all cz_frequencies
        for freq_index, cz_frequency in enumerate(cz_frequency_values):
            cz_clock = f'{coupler}.cz'
            cz_pulse_port = f'{coupler}:fl'
            schedule.add(
                SetClockFrequency(clock=cz_clock, clock_freq_new= - cz_frequency + 4.4e9),
            )

            # The inner for loop iterates over cz pulse durations
            for acq_index, cz_amplitude in enumerate(cz_pulse_amplitude_values):
                this_index = freq_index * number_of_amplitudes + acq_index

                relaxation = schedule.add(Reset(*qubits))

                for this_qubit in qubits:
                    schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                    # schedule.add(
                    #     Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                    #     ref_op=relaxation, ref_pt="end",
                    # )
                schedule.add(ResetClockPhase(clock=coupler+'.cz'))
                    #     ref_op=relaxation, ref_pt="end",)

                # cz_amplitude = 0.75
                # cz_duration = 200e-9
                # TODO MERGE-CZ-GATE: Where is cz_pulse_amplitude defined?
                cz = schedule.add(
                        SoftSquarePulse(
                            duration=cz_duration,
                            amp=cz_pulse_amplitude,
                            port=cz_pulse_port,
                            clock=cz_clock,
                        ),
                    )

                for this_qubit in qubits:
                    schedule.add(
                        Measure(this_qubit, acq_index=this_index, bin_mode=self.bin_mode),
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
