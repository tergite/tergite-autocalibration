"""
Module containing a schedule class for Ramsey calibration. (1D parameter sweep, for 2D see ramsey_detunings.py)
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X, CZ
from quantify_scheduler.operations.pulse_library import SuddenNetZeroPulse,ResetClockPhase,IdlePulse,DRAGPulse,SetClockFrequency,NumericalPulse,SoftSquarePulse,SquarePulse
from quantify_scheduler.operations.pulse_library import DRAGPulse,SetClockFrequency,NumericalPulse,SoftSquarePulse,SquarePulse, ResetClockPhase
from quantify_scheduler.resources import ClockResource
from calibration_schedules.measurement_base import Measurement
from utilities.extended_transmon_element import Measure_RO1, Rxy_12
from config_files.coupler_config import edge_group
from matplotlib import pyplot as plt

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
        schedule = Schedule("CZ_chevron",repetitions)
        qubits = coupler.split(sep='_')

        # cz_frequency_values = np.array(list(cz_pulse_frequencies_sweep.values())[0])
        cz_duration_values = list(cz_pulse_durations.values())[0]
        cz_pulse_amplitude_values = list(cz_pulse_amplitudes.values())[0]
        print(f'{ cz_duration_values = }')
        print(f'{ cz_pulse_amplitude_values = }')
        # print(f'{ cz_frequency_values[0] = }')

        # couplers_list = [coupler]
        # # find cz parameters from redis
        # redis_connection = redis.Redis(decode_responses=True)
        # cz_pulse_amplitude = {}
        # for this_coupler in couplers_list:
        #     qubits = this_coupler.split(sep='_')
        #     cz_amplitude_values = []
        #     for qubit in qubits: 
        #         redis_config = redis_connection.hgetall(f"transmons:{qubit}")
        #         cz_amplitude_values.append(float(redis_config['cz_pulse_amplitude']))
        #     cz_pulse_amplitude[this_coupler] = cz_amplitude_values[0]
        # print(f'{cz_pulse_amplitude = }')

        # schedule.add_resource(
        #     ClockResource(name=coupler+'.cz',freq= - cz_frequency_values[0] + 4.4e9)
        # )

        schedule.add_resource(
            ClockResource(name=coupler+'.cz',freq= 4.4e9)
        )

        number_of_durations = len(cz_duration_values)

        # The outer loop, iterates over all cz_frequencies
        for freq_index, cz_amplitude in enumerate(cz_pulse_amplitude_values):
            cz_clock = f'{coupler}.cz'
            cz_pulse_port = f'{coupler}:fl'
            # schedule.add(
            #     SetClockFrequency(clock=cz_clock, clock_freq_new= - cz_frequency + 4.4e9),
            # )
            # schedule.add(
            #     SetClockFrequency(clock=cz_clock, clock_freq_new=4.4e9),
            # )

            #The inner for loop iterates over cz pulse durations
            for acq_index, cz_duration in enumerate(cz_duration_values):
                this_index = freq_index * number_of_durations + acq_index

                relaxation = schedule.add(Reset(*qubits))

                # for this_qubit in qubits:
                    # schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                    # if this_qubit == 'q15':
                        # schedule.add(IdlePulse(20e-9))
                        # schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                        # schedule.add(Rxy_12(this_qubit))
                    # else:
                        # schedule.add(IdlePulse(20e-9))
                        # schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                        # schedule.add(Rxy_12(this_qubit))

                buffer = schedule.add(IdlePulse(4e-9))
                # schedule.add(
                # SetClockFrequency(clock=cz_clock, clock_freq_new=-1/cz_duration+4.4e9),
                # ) 
                schedule.add(ResetClockPhase(clock=coupler+'.cz'))
                # cz = schedule.add(DRAGPulse(
                #             duration=cz_duration,
                #             G_amp = cz_amplitude,
                #             D_amp = 0,
                #             port=cz_pulse_port,
                #             clock=cz_clock,
                #             phase=0,
                #         ),
                #     ) 

                cz = schedule.add(
                            SquarePulse(
                                duration = cz_duration,
                                amp = cz_amplitude,
                                port = cz_pulse_port,
                                clock = cz_clock,
                            ),
                        )
                # schedule.add(ResetClockPhase(clock=coupler+'.cz'))

                # cz = schedule.add(
                #             SoftSquarePulse(
                #                 duration = cz_duration,
                #                 amp = -cz_amplitude,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )
                

                # reset test
                # buffer = schedule.add(IdlePulse(cz_duration_values[-1]-cz_duration))
                # if this_qubit == 'q15':
                    # schedule.add(X90(this_qubit), ref_op=buffer, ref_pt='end')
                    # schedule.add(Rxy_12(this_qubit))
                # else:
                #     schedule.add(IdlePulse(20e-9))

                buffer = schedule.add(IdlePulse(4e-9))

                for this_qubit in qubits:
                    schedule.add(
                        Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                        ref_op=buffer,rel_time=12e-9, ref_pt="end",
                    )
        return schedule

class CZ_chevron_ac_reset(Measurement):
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
            redis_config = redis_connection.hgetall(f"couplers:{this_coupler}")
            cz_pulse_amplitude[this_coupler] = float(redis_config['cz_pulse_amplitude'])
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
                
                buffer = schedule.add(IdlePulse(4e-9))

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
