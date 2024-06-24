"""
Module containing a schedule class for Ramsey calibration. (1D parameter sweep, for 2D see ramsey_detunings.py)
"""
import numpy as np
from quantify_scheduler import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.control_flow_library import Loop
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X, CZ
from quantify_scheduler.operations.pulse_library import ResetClockPhase, SoftSquarePulse, IdlePulse
from quantify_scheduler.resources import ClockResource

from tergite_autocalibration.config.coupler_config import qubit_types
from tergite_autocalibration.config.settings import REDIS_CONNECTION
from tergite_autocalibration.lib.measurement_base import Measurement
from tergite_autocalibration.utils.extended_transmon_element import Measure_RO_Opt, Rxy_12
from tergite_autocalibration.utils.extended_coupler_edge import CompositeSquareEdge
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon
import itertools

class CZ_calibration(Measurement):

    def __init__(self, transmons: dict[str, ExtendedTransmon],couplers: dict[str, CompositeSquareEdge], qubit_state: int = 0):
        super().__init__(transmons)
        self.transmons = transmons
        self.qubit_state = qubit_state
        self.couplers = couplers

    def schedule_function(
        self,
        ramsey_phases: dict[str, np.ndarray],
        control_ons: dict[str, np.ndarray],
        dynamic: bool,
        swap_type: bool,
        use_edge:bool = False,
        number_of_cz: int = 1,
        repetitions: int = 2048,
        opt_cz_pulse_frequency: dict[str,float] = None,
        opt_cz_pulse_duration: dict[str,float] = None,
        opt_cz_pulse_amplitude: dict[str,float] = None,
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
        number_of_cz
            The number of CZ pulses to be applied.
        testing_group
            The edge group to be tested. 0 means all edges.
        ramsey_phases
            the phase of the second pi/2 pulse.
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """
        if dynamic:
            name = 'CZ_dynamic_phase'
        else:
            name = 'CZ_calibration'

        qubit_type_list = ['Control','Target']
        if swap_type:
            qubit_type_list.reverse()
            print('swapping')
            name += '_swap'

        schedule = Schedule(f"{name}", repetitions)
        all_couplers = self.couplers
        all_qubits = [coupler.split(sep='_') for coupler in all_couplers]
        all_qubits = sum(all_qubits, [])
        # target,control = np.transpose(qubits)[0],np.transpose(qubits)[1]

        # print(f'{all_qubits = }')

        # find cz parameters from redis

        cz_pulse_frequency, cz_pulse_duration, cz_pulse_amplitude = {}, {}, {}
        print(f'{opt_cz_pulse_amplitude = }')
        print(f'{opt_cz_pulse_frequency = }')
        print(f'{opt_cz_pulse_duration = }')
        for coupler in all_couplers:
            qubits = coupler.split(sep='_')
            for this_coupler in all_couplers:
                redis_config = REDIS_CONNECTION.hgetall(f"couplers:{this_coupler}")
                cz_pulse_frequency[this_coupler] = float(redis_config['cz_pulse_frequency'])
                cz_pulse_duration[this_coupler] = float(redis_config['cz_pulse_duration'])
                cz_pulse_amplitude[this_coupler] = float(redis_config['cz_pulse_amplitude'])
                if opt_cz_pulse_amplitude is not None:
                    cz_pulse_amplitude[this_coupler] += opt_cz_pulse_amplitude[this_coupler]
                if opt_cz_pulse_frequency is not None:
                    cz_pulse_frequency[this_coupler] += opt_cz_pulse_frequency[this_coupler]
                if opt_cz_pulse_duration is not None:
                    cz_pulse_duration[this_coupler] += opt_cz_pulse_duration[this_coupler]

        print(f'{cz_pulse_frequency = }')
        print(f'{cz_pulse_duration = }')
        print(f'{cz_pulse_amplitude = }')


        for index, this_coupler in enumerate(all_couplers):
            if this_coupler in ['q21_q22','q22_q23','q23_q24','q24_q25']:
                downconvert = 0
            else:
                downconvert = 4.4e9
            schedule.add_resource(
                ClockResource(name=f'{this_coupler}.cz', freq=-cz_pulse_frequency[this_coupler] + downconvert)
                # ClockResource(name=f'{this_coupler}.cz', freq=0)
            )

        ramsey_phases_values = ramsey_phases[all_qubits[0]]
        number_of_phases = len(ramsey_phases_values)
        control_on_values = control_ons[all_qubits[0]]

        for cz_index, control_on in enumerate(control_on_values):
            for ramsey_index, ramsey_phase in enumerate(ramsey_phases_values[:-2]):
                relaxation = schedule.add(Reset(*all_qubits), label=f"Reset_{cz_index}_{ramsey_index}")

                gate_amp = 1
                if dynamic:
                    if not control_on:
                        gate_amp = 0
                    else:
                        gate_amp = 1
                else:
                    if control_on:
                        for this_qubit in all_qubits:
                            if qubit_types[this_qubit] == qubit_type_list[0]:
                                x = schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                for this_qubit in all_qubits:
                    if qubit_types[this_qubit] == qubit_type_list[1]:
                        x90 = schedule.add(X90(this_qubit), ref_op=relaxation, ref_pt='end')

                buffer_start = schedule.add(IdlePulse(4e-9), ref_op=x90, ref_pt='end')
                for this_coupler in all_couplers:
                    cz_clock = f'{this_coupler}.cz'
                    cz_pulse_port = f'{this_coupler}:fl'
                    reset_phase = schedule.add(ResetClockPhase(clock=cz_clock),
                                               ref_op=buffer_start, ref_pt='end', )
                    for i in range(number_of_cz):
                        if use_edge:
                            # print(qubits[0],qubits[1])
                            cz = schedule.add(CZ(qubits[0],qubits[1]))
                        else:
                            # print(this_coupler,cz_pulse_port,cz_clock)
                            cz = schedule.add(
                                SoftSquarePulse(
                                    duration=cz_pulse_duration[this_coupler],
                                    amp=cz_pulse_amplitude[this_coupler]*gate_amp,
                                    port=cz_pulse_port,
                                    clock=cz_clock,
                                )
                            )
                        # buffer_end = schedule.add(IdlePulse(100e-9))

                buffer_end = schedule.add(IdlePulse(4e-9))

                if not dynamic:
                    if control_on:
                        for this_qubit in all_qubits:
                            if qubit_types[this_qubit] == qubit_type_list[0]:
                                # print(this_qubit, qubit_types[this_qubit])
                                x_end = schedule.add(X(this_qubit), ref_op=buffer_end, ref_pt='end')
                                # pass

                for this_qubit in all_qubits:
                    if qubit_types[this_qubit] == qubit_type_list[1]:
                        x90_end = schedule.add(Rxy(theta=90, phi=ramsey_phase, qubit=this_qubit), ref_op=buffer_end,
                                               ref_pt='end')

                for this_qubit in all_qubits:
                    this_index = cz_index * number_of_phases + ramsey_index
                    schedule.add(Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                                 ref_op=x90_end, ref_pt="end", )

                    # 0 calibration point
            calib = schedule.add(IdlePulse(4e-9))
            for this_qubit in all_qubits:
                schedule.add(Reset(this_qubit),ref_op=calib,ref_pt='end')
                schedule.add(Measure(this_qubit, acq_index=this_index+1, bin_mode=BinMode.AVERAGE))

                # 1 calibration point
                schedule.add(Reset(this_qubit))
                schedule.add(X(this_qubit))
                schedule.add(Measure(this_qubit, acq_index=this_index+2, bin_mode=BinMode.AVERAGE))
                schedule.add(Reset(this_qubit))
        return schedule



class CZ_calibration_SSRO(Measurement):

    def __init__(self, transmons: dict[str, ExtendedTransmon],couplers: dict[str, CompositeSquareEdge], qubit_state: int = 0):
        super().__init__(transmons)
        self.transmons = transmons
        self.qubit_state = qubit_state
        self.couplers = couplers


    def schedule_function(
        self,
        ramsey_phases: dict[str,np.ndarray],
        swap_type: bool,
        dynamic: bool,
        control_ons: dict[str,np.ndarray],
        repetitions: int = 1024,
        opt_cz_pulse_frequency: dict[str,float] = None,
        opt_cz_pulse_duration: dict[str,float] = None,
        opt_cz_pulse_amplitude: dict[str,float] = None,

    ) -> Schedule:




        if dynamic:
            name = 'CZ_dynamic_phase_ssro'
        else:
            if swap_type:
                name = 'cz_calibration_swap_ssro'
            else:
                name = 'cz_calibration_ssro'
        schedule = Schedule(f"{name}")

        qubit_type_list = ['Control','Target']
        if swap_type:
            qubit_type_list.reverse()
            print('swapping')
            name += '_swap'

        all_couplers = self.couplers
        all_qubits = [coupler.split(sep='_') for coupler in all_couplers]
        print('these are all couplers: ', all_couplers)
        print('these are all qubits: ', all_qubits)
        all_qubits = sum(all_qubits, [])



        # The outer for-loop iterates over all qubits:
        shot = Schedule(f"shot")
        shot.add(IdlePulse(16e-9))

        #Initialize ClockResource with the first frequency value
        for this_qubit, this_transmon in self.transmons.items():
            ro_frequency = this_transmon.extended_clock_freqs.readout_3state_opt()
            schedule.add_resource(
                ClockResource(name=f'{this_qubit}.ro_3st_opt', freq=ro_frequency)
            )
            mw_frequency_01 = this_transmon.clock_freqs.f01()
            schedule.add_resource(
                ClockResource(name=f'{this_qubit}.01', freq=mw_frequency_01)
            )
            mw_frequency_12 = this_transmon.clock_freqs.f12()
            schedule.add_resource(
                ClockResource(name=f'{this_qubit}.12', freq=mw_frequency_12)
            )

        for index, this_coupler in enumerate(all_couplers):
            if this_coupler in ['q21_q22','q22_q23','q23_q24','q24_q25']:
                downconvert = 0
            else:
                downconvert = 4.4e9

        cz_pulse_frequency, cz_pulse_duration, cz_pulse_amplitude = {}, {}, {}
        for coupler in all_couplers:
            qubits = coupler.split(sep='_')
            for this_coupler in all_couplers:
                redis_config = REDIS_CONNECTION.hgetall(f"couplers:{this_coupler}")
                cz_pulse_frequency[this_coupler] = float(redis_config['cz_pulse_frequency'])
                cz_pulse_duration[this_coupler] = float(redis_config['cz_pulse_duration'])
                cz_pulse_amplitude[this_coupler] = float(redis_config['cz_pulse_amplitude'])
                if opt_cz_pulse_amplitude is not None:
                    cz_pulse_amplitude[this_coupler] += opt_cz_pulse_amplitude[this_coupler]
                if opt_cz_pulse_frequency is not None:
                    cz_pulse_frequency[this_coupler] += opt_cz_pulse_frequency[this_coupler]
                if opt_cz_pulse_duration is not None:
                    cz_pulse_duration[this_coupler] += opt_cz_pulse_duration[this_coupler]

        print(f'{cz_pulse_frequency = }')
        print(f'{cz_pulse_duration = }')
        print(f'{cz_pulse_amplitude = }')

        for index, this_coupler in enumerate(all_couplers):
            schedule.add_resource(
                ClockResource(name=f'{this_coupler}.cz', freq=-cz_pulse_frequency[this_coupler] + 4.4e9))
            shot.add_resource(ClockResource(name=f'{this_coupler}.cz', freq=-cz_pulse_frequency[this_coupler] + 4.4e9))
        # print(ramsey_phases,qubits)

        ramsey_phases_values = ramsey_phases[all_qubits[0]]
        number_of_phases = len(ramsey_phases_values) + 3  # +3 for calibration points
        control_on_values = control_ons[all_qubits[0]]

        state = ['g','e','f']
        states =list(itertools.product(state, state))

        for cz_index, control_on in enumerate(control_on_values):
            for ramsey_index, ramsey_phase in enumerate(ramsey_phases_values):
                relaxation = shot.add(Reset(*all_qubits), label=f"Reset_{cz_index}_{ramsey_index}")

                # cz_amplitude = 0.5
                if dynamic:
                    if not control_on:
                        for this_coupler in all_couplers:
                            cz_pulse_amplitude[this_coupler] = 0
                else:
                    if control_on:
                        for this_qubit in all_qubits:
                            if qubit_types[this_qubit] == qubit_type_list[0]:
                                #pass
                                x = shot.add(X(this_qubit), ref_op=relaxation, ref_pt='end')

                for this_qubit in all_qubits:
                    if qubit_types[this_qubit] == qubit_type_list[1]:
                        #x = shot.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                        #pass
                        x90 = shot.add(X90(this_qubit), ref_op=relaxation, ref_pt='end')

                #buffer_start = shot.add(IdlePulse(8e-9), ref_op=x90, ref_pt='end')
                buffer_start = shot.add(IdlePulse(12e-9), ref_op=x90, ref_pt='end')

                for this_coupler in all_couplers:
                    cz_clock = f'{this_coupler}.cz'
                    cz_pulse_port = f'{this_coupler}:fl'

                    reset_phase = shot.add(ResetClockPhase(clock=cz_clock),
                                          ref_op=buffer_start, ref_pt='end', )
                    cz = shot.add(
                        SoftSquarePulse(
                            duration=cz_pulse_duration[this_coupler],
                            amp=cz_pulse_amplitude[this_coupler],
                            port=cz_pulse_port,
                            clock=cz_clock,
                            # port = 'q11_q12:fl',
                            # clock = 'q11_q12.cz',
                        )
                    )
                    # cz =  shot.add(IdlePulse(212e-9))
                buffer_end = shot.add(IdlePulse(8e-9), ref_op=buffer_start, ref_pt='end',
                                      rel_time=np.ceil(cz_pulse_duration[this_coupler] * 1e9 / 4) * 4e-9)
                if not dynamic:
                    if control_on:
                        for this_qubit in all_qubits:
                            if qubit_types[this_qubit] == qubit_type_list[0]:
                                #pass
                                x_end = shot.add(X(this_qubit), ref_op=buffer_end, ref_pt='end')


                for this_qubit in all_qubits:
                    if qubit_types[this_qubit] == qubit_type_list[1]:
                        #x_end = shot.add(X(this_qubit), ref_op=buffer_end, ref_pt='end')
                        #pass
                        x90_end = shot.add(Rxy(theta=90, phi=ramsey_phase, qubit=this_qubit), ref_op=buffer_end,
                                           ref_pt='end')

                shot.add(IdlePulse(12e-9))
                for this_qubit in all_qubits:
                    this_index = cz_index * number_of_phases + ramsey_index

                    shot.add(Measure_RO_Opt(this_qubit, acq_index=this_index, bin_mode=BinMode.APPEND),
                             ref_op=buffer_end, ref_pt="end", )
                #relaxation = shot.add(Reset(*all_qubits), label=f"Reset_End_{cz_index}_{ramsey_index}")

            # Calibration points
            root_relaxation = shot.add(Reset(*all_qubits), label=f"Reset_Calib_{cz_index}")

            for this_qubit in all_qubits:
                qubit_levels = range(self.qubit_state + 1)
                number_of_levels = len(qubit_levels)

                shot.add(Reset(*all_qubits), ref_op=root_relaxation,
                         ref_pt_new='end')  # To enforce parallelism we refer to the root relaxation
                # The intermediate for-loop iterates over all ro_amplitudes:
                # for ampl_indx, ro_amplitude in enumerate(ro_amplitude_values):
                # The inner for-loop iterates over all qubit levels:
                for level_index, state_level in enumerate(qubit_levels):
                    calib_index = this_index + level_index + 1
                    # print(f'{calib_index = }')
                    if state_level == 0:
                        prep = shot.add(IdlePulse(40e-9))
                    elif state_level == 1:
                        prep = shot.add(X(this_qubit), )
                    elif state_level == 2:
                        shot.add(X(this_qubit), )
                        prep = shot.add(Rxy_12(this_qubit), )
                    else:
                        raise ValueError('State Input Error')
                    shot.add(Measure_RO_Opt(this_qubit, acq_index=calib_index, bin_mode=BinMode.APPEND),
                             ref_op=prep, ref_pt="end", )
                    shot.add(Reset(this_qubit))
        shot.add(IdlePulse(16e-9))

        schedule.add(IdlePulse(16e-9))
        print(schedule.add(shot, control_flow=Loop(repetitions), validate=False))
        schedule.add(IdlePulse(16e-9))
        return schedule



class CZ_calibration_duration(Measurement):

    def __init__(self, transmons, coupler, qubit_state: int = 0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.coupler = coupler
        self.static_kwargs = {
            'qubits': self.qubits,
            # 'mw_frequencies': self.attributes_dictionary('f01'),
            # 'mw_pulse_durations': self.attributes_dictionary('duration'),
            # 'mw_pulse_ports': self.attributes_dictionary('microwave'),
            'mw_ef_amps180': self.attributes_dictionary('ef_amp180'),
            'mw_frequencies_12': self.attributes_dictionary('f12'),
            # 'cz_pulse_width': self.attributes_dictionary('cz_pulse_width'),
            # 'cz_pulse_amplitude': self.attributes_dictionary('cz_pulse_amplitude'),
            'coupler': self.coupler,
            # 'cz_pulse_duration': self.attributes_dictionary('cz_pulse_duration'),
            # 'cz_pulse_frequency': self.attributes_dictionary('cz_pulse_frequency'),
        }

    def schedule_function(
            self,
            qubits: list[str],
            mw_ef_amps180: dict[str, float],
            # mw_frequencies: dict[str,float],
            mw_frequencies_12: dict[str, float],
            # mw_pulse_ports: dict[str,str],
            # mw_pulse_durations: dict[str,float],
            # cz_pulse_amplitude: dict[str,float],
            # cz_pulse_width: dict[str,float], 
            # testing_group: int = 1,
            coupler: str,
            # cz_pulse_frequency: dict[str,float],
            # cz_pulse_duration: dict[str,float],
            ramsey_phases: dict[str, np.ndarray],
            control_ons: dict[str, np.ndarray],
            number_of_cz: int = 1,
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
        number_of_cz
            The number of CZ pulses to be applied.
        testing_group
            The edge group to be tested. 0 means all edges.
        ramsey_phases
            the phase of the second pi/2 pulse.
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """
        dynamic = False
        if dynamic:
            name = 'CZ_dynamic_phase'
        else:
            name = 'CZ_calibration'
        schedule = Schedule(f"{name}", repetitions)




        all_couplers = [coupler]
        qubits = [coupler.split(sep='_') for coupler in all_couplers]
        target, control = np.transpose(qubits)[0], np.transpose(qubits)[1]
        print(f'{qubits = }')
        print(f'{target = }')
        print(f'{control = }')

        # find cz parameters from redis

        cz_pulse_frequency, cz_pulse_duration, cz_pulse_amplitude = {}, {}, {}
        for coupler in all_couplers:
            qubits = coupler.split(sep='_')
            cz_frequency_values, cz_duration_values, cz_amplitude_values = [], [], []
            for qubit in qubits:
                redis_config = REDIS_CONNECTION.hgetall(f"transmons:{qubit}")
                cz_frequency_values.append(float(redis_config['cz_pulse_frequency']))
                cz_duration_values.append(float(redis_config['cz_pulse_duration']))

            cz_pulse_frequency[coupler] = cz_frequency_values[0]
            cz_pulse_duration[coupler] = cz_duration_values[0]
            cz_pulse_amplitude[coupler] = cz_amplitude_values[0]
        print(f'{cz_pulse_frequency = }')
        print(f'{cz_pulse_amplitude = }')

        # Add the clocks to the schedule
        # for this_qubit, mw_f_val in mw_frequencies.items():
        #     schedule.add_resource(
        #         ClockResource( name=f'{this_qubit}.01', freq=mw_f_val)
        #     )
        for this_qubit, mw_f_val in mw_frequencies_12.items():
            schedule.add_resource(
                ClockResource(name=f'{this_qubit}.12', freq=mw_f_val)
            )
        for index, this_coupler in enumerate(all_couplers):
            schedule.add_resource(
                ClockResource(name=f'{this_coupler}.cz', freq=-cz_pulse_frequency[this_coupler] + 4.4e9)
            )
            # self.couplers[this_coupler].cz.square_duration(cz_pulse_duration[this_coupler])
            # self.couplers[this_coupler].cz.square_amp(0.2)

        ramsey_phases_values = ramsey_phases[qubits[0]]
        number_of_phases = len(ramsey_phases_values)
        control_on_values = control_ons[qubits[0]]

        for cz_index, control_on in enumerate(control_on_values):
            for ramsey_index, ramsey_phase in enumerate(ramsey_phases_values):
                relaxation = schedule.add(Reset(*qubits), label=f"Reset_{cz_index}_{ramsey_index}")

                cz_amplitude = 0.62
                if dynamic:
                    if not control_on:
                        cz_amplitude = 0
                else:
                    if control_on:
                        for this_qubit in control:
                            x = schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')

                for this_qubit in target:
                    x90 = schedule.add(X90(this_qubit), ref_op=relaxation, ref_pt='end')

                for this_coupler in all_couplers:
                    cz_clock = f'{this_coupler}.cz'
                    cz_pulse_port = f'{this_coupler}:fl'
                    cz = schedule.add(
                        SoftSquarePulse(
                            duration=cz_pulse_duration[this_coupler],
                            amp=cz_amplitude,
                            port=cz_pulse_port,
                            clock=cz_clock,
                        ),
                        ref_op=x90, ref_pt='end',
                    )
                if not dynamic:
                    if control_on:
                        for this_qubit in control:
                            x_end = schedule.add(X(this_qubit), ref_op=cz, ref_pt='end')

                for this_qubit in target:
                    x90_end = schedule.add(Rxy(theta=90, phi=ramsey_phase, qubit=this_qubit), ref_op=cz, ref_pt='end')

                for this_qubit in qubits:
                    this_index = cz_index * number_of_phases + ramsey_index
                    schedule.add(Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                                 ref_op=x90_end, ref_pt="end", )

        return schedule
