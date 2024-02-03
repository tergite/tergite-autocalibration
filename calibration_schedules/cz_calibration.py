"""
Module containing a schedule class for Ramsey calibration. (1D parameter sweep, for 2D see ramsey_detunings.py)
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X, CZ
from quantify_scheduler.operations.pulse_library import ResetClockPhase,DRAGPulse,SetClockFrequency,NumericalPulse,SoftSquarePulse,SquarePulse,IdlePulse
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.resources import ClockResource
from calibration_schedules.measurement_base import Measurement
from utilities.extended_transmon_element import Measure_RO1, Measure_RO_Opt, Rxy_12
from quantify_scheduler.operations.control_flow_library import Loop
from config_files.coupler_config import edge_group, qubit_types
from scipy.signal import gaussian
from scipy import signal
from matplotlib import pyplot as plt
import numpy as np

import redis

class CZ_calibration(Measurement):

    def __init__(self,transmons,coupler,qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.coupler = coupler
        self.static_kwargs = {
            'qubits': self.qubits,
            # 'mw_frequencies': self.attributes_dictionary('f01'),
            # 'mw_pulse_durations': self.attributes_dictionary('duration'),
            # 'mw_pulse_ports': self.attributes_dictionary('microwave'),
            # 'mw_ef_amps180': self.attributes_dictionary('ef_amp180'),
            # 'mw_frequencies_12': self.attributes_dictionary('f12'),
            # 'cz_pulse_width': self.attributes_dictionary('cz_pulse_width'),
            # 'cz_pulse_amplitude': self.attributes_dictionary('cz_pulse_amplitude'),
            'coupler': self.coupler,
            # 'cz_pulse_duration': self.attributes_dictionary('cz_pulse_duration'),
            # 'cz_pulse_frequency': self.attributes_dictionary('cz_pulse_frequency'),
        }

    def schedule_function(
            self,
            qubits: list[str],
            # mw_ef_amps180: dict[str,float],
            # mw_frequencies: dict[str,float],
            # mw_frequencies_12: dict[str,float],
            # mw_pulse_ports: dict[str,str],
            # mw_pulse_durations: dict[str,float],
            # cz_pulse_amplitude: dict[str,float],
            # cz_pulse_width: dict[str,float], 
            # testing_group: int = 1,
            coupler: str,
            # cz_pulse_frequency: dict[str,float],
            # cz_pulse_duration: dict[str,float],
            ramsey_phases: dict[str,np.ndarray],
            control_ons: dict[str,np.ndarray],
            number_of_cz: int = 1,
            repetitions: int = 4096,
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
        schedule = Schedule(f"{name}",repetitions)

        # all_couplers_all = edge_group.keys()
        # all_couplers,bus_list = [],[]

        all_couplers = [coupler]
        all_qubits = [coupler.split(sep='_') for coupler in all_couplers]
        all_qubits =  sum(all_qubits, [])
        # target,control = np.transpose(qubits)[0],np.transpose(qubits)[1]
        
        print(f'{all_qubits = }')

        # find cz parameters from redis
        redis_connection = redis.Redis(decode_responses=True)
        cz_pulse_frequency,cz_pulse_duration,cz_pulse_amplitude = {},{},{}
        for coupler in all_couplers:
            qubits = coupler.split(sep='_')
            for this_coupler in all_couplers:
                redis_config = redis_connection.hgetall(f"couplers:{this_coupler}")
                cz_pulse_frequency[this_coupler] = float(redis_config['cz_pulse_frequency'])
                cz_pulse_duration[this_coupler] = np.ceil(float(redis_config['cz_pulse_duration'])* 1e9 / 4) * 4e-9
                cz_pulse_amplitude[this_coupler] = float(redis_config['cz_pulse_amplitude'])
        print(f'{cz_pulse_frequency = }')
        print(f'{cz_pulse_duration = }')
        print(f'{cz_pulse_amplitude = }')
        

        # Add the clocks to the schedule
        # for this_qubit, mw_f_val in mw_frequencies.items():
        #     schedule.add_resource(
        #         ClockResource( name=f'{this_qubit}.01', freq=mw_f_val)
        #     )
        # for this_qubit, mw_f_val in mw_frequencies_12.items():
        #     schedule.add_resource(
        #         ClockResource(name=f'{this_qubit}.12', freq=mw_f_val)
        #     )
        for index, this_coupler in enumerate(all_couplers):
            if this_coupler == 'q16_q21':
                downconvert = 0
            else:
                downconvert = 4.4e9
            schedule.add_resource(
                ClockResource(name=f'{this_coupler}.cz', freq=-cz_pulse_frequency[this_coupler]+downconvert)
            )
        
        ramsey_phases_values = ramsey_phases[all_qubits[0]]
        number_of_phases = len(ramsey_phases_values)
        control_on_values = control_ons[all_qubits[0]]

        for cz_index,control_on in enumerate(control_on_values):
            for ramsey_index, ramsey_phase in enumerate(ramsey_phases_values): 
                relaxation = schedule.add(Reset(*all_qubits), label=f"Reset_{cz_index}_{ramsey_index}")
    
                # cz_amplitude = 0.5
                if dynamic:
                    if not control_on:
                        for this_coupler in all_couplers:
                            cz_pulse_amplitude[this_coupler] = 0
                else:
                    if control_on:
                        for this_qubit in all_qubits:
                            if qubit_types[this_qubit] == 'Control':
                                x = schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                for this_qubit in all_qubits:
                    if qubit_types[this_qubit] == 'Target':
                        x90 = schedule.add(X90(this_qubit), ref_op=relaxation, ref_pt='end')

                buffer_start = schedule.add(IdlePulse(4e-9), ref_op=x90, ref_pt='end')
                for this_coupler in all_couplers:
                    cz_clock = f'{this_coupler}.cz'
                    cz_pulse_port = f'{this_coupler}:fl'
                    reset_phase = schedule.add(ResetClockPhase(clock=cz_clock),
                            ref_op=buffer_start, ref_pt='end',)
                    cz = schedule.add(
                            SoftSquarePulse(
                                duration=cz_pulse_duration[this_coupler],
                                amp = cz_pulse_amplitude[this_coupler],
                                port=cz_pulse_port,
                                clock=cz_clock,
                            )
                        )
                    # cz = schedule.add(IdlePulse(cz_pulse_duration[this_coupler]))
                buffer_end = schedule.add(IdlePulse(4e-9),ref_op=buffer_start, ref_pt='end',rel_time = np.ceil( cz_pulse_duration[this_coupler] * 1e9 / 4) * 4e-9)
                if not dynamic:
                    if control_on:
                        for this_qubit in all_qubits:
                            if qubit_types[this_qubit] == 'Control':
                                # print(this_qubit, qubit_types[this_qubit])
                                x_end = schedule.add(X(this_qubit), ref_op=buffer_end, ref_pt='end')
                
                for this_qubit in all_qubits:
                    if qubit_types[this_qubit] == 'Target':
                        x90_end = schedule.add(Rxy(theta=90, phi=ramsey_phase, qubit=this_qubit), ref_op=buffer_end, ref_pt='end')
                
                for this_qubit in all_qubits:
                    this_index = cz_index*number_of_phases+ramsey_index
                    schedule.add(Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                                    ref_op=x90_end, ref_pt="end",)
        return schedule

class CZ_dynamic_phase(Measurement):

    def __init__(self,transmons,coupler,qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.coupler = coupler
        self.static_kwargs = {
            'qubits': self.qubits,
            # 'mw_frequencies': self.attributes_dictionary('f01'),
            # 'mw_pulse_durations': self.attributes_dictionary('duration'),
            # 'mw_pulse_ports': self.attributes_dictionary('microwave'),
            # 'mw_ef_amps180': self.attributes_dictionary('ef_amp180'),
            # 'mw_frequencies_12': self.attributes_dictionary('f12'),
            # 'cz_pulse_width': self.attributes_dictionary('cz_pulse_width'),
            # 'cz_pulse_amplitude': self.attributes_dictionary('cz_pulse_amplitude'),
            'coupler': self.coupler,
            # 'cz_pulse_duration': self.attributes_dictionary('cz_pulse_duration'),
            # 'cz_pulse_frequency': self.attributes_dictionary('cz_pulse_frequency'),
        }

    def schedule_function(
            self,
            qubits: list[str],
            # mw_ef_amps180: dict[str,float],
            # mw_frequencies: dict[str,float],
            # mw_frequencies_12: dict[str,float],
            # mw_pulse_ports: dict[str,str],
            # mw_pulse_durations: dict[str,float],
            # cz_pulse_amplitude: dict[str,float],
            # cz_pulse_width: dict[str,float], 
            # testing_group: int = 1,
            coupler: str,
            # cz_pulse_frequency: dict[str,float],
            # cz_pulse_duration: dict[str,float],
            ramsey_phases: dict[str,np.ndarray],
            control_ons: dict[str,np.ndarray],
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
        dynamic = True
        if dynamic:
            name = 'CZ_dynamic_phase'
        else:
            name = 'CZ_calibration'
        schedule = Schedule(f"{name}",repetitions)

        # all_couplers_all = edge_group.keys()
        # all_couplers,bus_list = [],[]
        # for coupler in all_couplers_all:
        #     control,target = coupler.split('_')[0], coupler.split('_')[1]
        #     if self.testing_group != 0:
        #         check = edge_group[coupler] == self.testing_group
        #     else:
        #         check = True
        #     if control in qubits and target in qubits and check:
        #         bus_list.append([control,target])
        #         all_couplers.append(coupler)
        # control, target = np.transpose(bus_list)
        # # cz_duration, cz_width = 200e-9, 4e-9
        # # placeholder for the CZ pulse frequency and amplitude -0.4 689.9058811833632 for parking current  = -35e-6
        # cz_pulse_frequency = {coupler: -0.4e6 for coupler in all_couplers}
        # cz_pulse_duration = {coupler: 688e-09 for coupler in all_couplers}
        # # cz_pulse_amplitude = {coupler: 0 for coupler in all_couplers}
        # # print(f'{cz_pulse_duration = }')
        # # print(f'{cz_pulse_frequency = }')
        all_couplers = [coupler]
        all_qubits = [coupler.split(sep='_') for coupler in all_couplers]
        all_qubits =  sum(all_qubits, [])
        # target,control = np.transpose(qubits)[0],np.transpose(qubits)[1]
        
        print(f'{all_qubits = }')

        # find cz parameters from redis
        redis_connection = redis.Redis(decode_responses=True)
        cz_pulse_frequency,cz_pulse_duration,cz_pulse_amplitude = {},{},{}
        for coupler in all_couplers:
            qubits = coupler.split(sep='_')
            for this_coupler in all_couplers:
                redis_config = redis_connection.hgetall(f"couplers:{this_coupler}")
                cz_pulse_frequency[this_coupler] = float(redis_config['cz_pulse_frequency'])
                cz_pulse_duration[this_coupler] = np.ceil(float(redis_config['cz_pulse_duration'])* 1e9 / 4) * 4e-9
                cz_pulse_amplitude[this_coupler] = float(redis_config['cz_pulse_amplitude'])
        print(f'{cz_pulse_frequency = }')
        print(f'{cz_pulse_duration = }')
        print(f'{cz_pulse_amplitude = }')

        # Add the clocks to the schedule
        # for this_qubit, mw_f_val in mw_frequencies.items():
        #     schedule.add_resource(
        #         ClockResource( name=f'{this_qubit}.01', freq=mw_f_val)
        #     )
        # for this_qubit, mw_f_val in mw_frequencies_12.items():
        #     schedule.add_resource(
        #         ClockResource(name=f'{this_qubit}.12', freq=mw_f_val)
        #     )
        for index, this_coupler in enumerate(all_couplers):
            schedule.add_resource(
                ClockResource(name=f'{this_coupler}.cz', freq=-cz_pulse_frequency[this_coupler]+4.4e9)
            )
        
        ramsey_phases_values = ramsey_phases[all_qubits[0]]
        number_of_phases = len(ramsey_phases_values)
        control_on_values = control_ons[all_qubits[0]]

        for cz_index,control_on in enumerate(control_on_values):
            for ramsey_index, ramsey_phase in enumerate(ramsey_phases_values): 
                relaxation = schedule.add(Reset(*all_qubits), label=f"Reset_{cz_index}_{ramsey_index}")
    
                # cz_amplitude = 0.5
                if dynamic:
                    if not control_on:
                        for this_coupler in all_couplers:
                            cz_amplitude = 0
                    else:
                        cz_amplitude = 1
                else:
                    if control_on:
                        for this_qubit in all_qubits:
                            if qubit_types[this_qubit] == 'Control':
                                x = schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                for this_qubit in all_qubits:
                    if qubit_types[this_qubit] == 'Target':
                        x90 = schedule.add(X90(this_qubit), ref_op=relaxation, ref_pt='end')

                for this_coupler in all_couplers:
                    cz_clock = f'{this_coupler}.cz'
                    cz_pulse_port = f'{this_coupler}:fl'
                    buffer = schedule.add(IdlePulse(4e-9), ref_op=x90, ref_pt='end')
                    reset_phase = schedule.add(ResetClockPhase(clock=cz_clock))
                    cz = schedule.add(
                            SoftSquarePulse(
                                duration=cz_pulse_duration[this_coupler],
                                amp = cz_pulse_amplitude[this_coupler]*cz_amplitude,
                                port=cz_pulse_port,
                                clock=cz_clock,
                            ),
                            ref_op=reset_phase, ref_pt='end',
                        )
                    # cz = schedule.add(IdlePulse(cz_pulse_duration[this_coupler]))
                    buffer = schedule.add(IdlePulse(4e-9))
                if not dynamic:
                    if control_on:
                        for this_qubit in all_qubits:
                            if qubit_types[this_qubit] == 'Control':
                                # print(this_qubit, qubit_types[this_qubit])
                                x_end = schedule.add(X(this_qubit), ref_op=buffer, ref_pt='end')
                
                for this_qubit in all_qubits:
                    if qubit_types[this_qubit] == 'Target':
                        x90_end = schedule.add(Rxy(theta=90, phi=ramsey_phase, qubit=this_qubit), ref_op=buffer, ref_pt='end')
                
                for this_qubit in all_qubits:
                    this_index = cz_index*number_of_phases+ramsey_index
                    schedule.add(Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                                    ref_op=x90_end, ref_pt="end",)
        return schedule



class CZ_calibration_duration(Measurement):

    def __init__(self,transmons,coupler,qubit_state:int=0):
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
            mw_ef_amps180: dict[str,float],
            # mw_frequencies: dict[str,float],
            mw_frequencies_12: dict[str,float],
            # mw_pulse_ports: dict[str,str],
            # mw_pulse_durations: dict[str,float],
            # cz_pulse_amplitude: dict[str,float],
            # cz_pulse_width: dict[str,float], 
            # testing_group: int = 1,
            coupler: str,
            # cz_pulse_frequency: dict[str,float],
            # cz_pulse_duration: dict[str,float],
            ramsey_phases: dict[str,np.ndarray],
            control_ons: dict[str,np.ndarray],
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
        schedule = Schedule(f"{name}",repetitions)

        # all_couplers_all = edge_group.keys()
        # all_couplers,bus_list = [],[]
        # for coupler in all_couplers_all:
        #     control,target = coupler.split('_')[0], coupler.split('_')[1]
        #     if self.testing_group != 0:
        #         check = edge_group[coupler] == self.testing_group
        #     else:
        #         check = True
        #     if control in qubits and target in qubits and check:
        #         bus_list.append([control,target])
        #         all_couplers.append(coupler)
        # control, target = np.transpose(bus_list)
        # # cz_duration, cz_width = 200e-9, 4e-9
        # # placeholder for the CZ pulse frequency and amplitude -0.4 689.9058811833632 for parking current  = -35e-6
        # cz_pulse_frequency = {coupler: -0.4e6 for coupler in all_couplers}
        # cz_pulse_duration = {coupler: 688e-09 for coupler in all_couplers}
        # # cz_pulse_amplitude = {coupler: 0 for coupler in all_couplers}
        # # print(f'{cz_pulse_duration = }')
        # # print(f'{cz_pulse_frequency = }')

        all_couplers = [coupler]
        qubits = [coupler.split(sep='_') for coupler in all_couplers]
        target,control = np.transpose(qubits)[0],np.transpose(qubits)[1]
        print(f'{qubits = }')
        print(f'{target = }')
        print(f'{control = }')

        # find cz parameters from redis
        redis_connection = redis.Redis(decode_responses=True)
        cz_pulse_frequency,cz_pulse_duration,cz_pulse_amplitude = {},{},{}
        for coupler in all_couplers:
            qubits = coupler.split(sep='_')
            cz_frequency_values,cz_duration_values,cz_amplitude_values = [],[],[]
            for qubit in qubits: 
                redis_config = redis_connection.hgetall(f"transmons:{qubit}")
                cz_frequency_values.append(float(redis_config['cz_pulse_frequency']))
                cz_duration_values.append(float(redis_config['cz_pulse_duration']))
                cz_amplitude_values.append(float(redis_config['cz_pulse_amplitude']))
            # cz_pulse_frequency[coupler] = np.mean(cz_frequency_values)
            # cz_pulse_duration[coupler] = np.ceil(np.mean(cz_duration_values) * 1e9 / 4) * 4e-9
            # cz_pulse_frequency[coupler] = 449.5e6
            # cz_pulse_duration[coupler] = 200e-9
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
                ClockResource(name=f'{this_coupler}.cz', freq=-cz_pulse_frequency[this_coupler]+4.4e9)
            )
            # self.couplers[this_coupler].cz.square_duration(cz_pulse_duration[this_coupler])
            # self.couplers[this_coupler].cz.square_amp(0.2)
        
        ramsey_phases_values = ramsey_phases[qubits[0]]
        number_of_phases = len(ramsey_phases_values)
        control_on_values = control_ons[qubits[0]]

        for cz_index,control_on in enumerate(control_on_values):
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
                                amp = cz_amplitude,
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
                    this_index = cz_index*number_of_phases+ramsey_index
                    schedule.add(Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                                    ref_op=x90_end, ref_pt="end",)
                # schedule.add(Reset(this_qubit))
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
        return schedule


class CZ_calibration_SSRO(Measurement):

    def __init__(self,transmons,coupler,qubit_state:int=0):
        super().__init__(transmons)

        self.transmons = transmons
        self.coupler = coupler
        self.qubit_state = qubit_state
        self.static_kwargs = {
            'qubits': self.qubits,

            'mw_frequencies': self.attributes_dictionary('f01'),
            'mw_amplitudes': self.attributes_dictionary('amp180'),
            'mw_pulse_durations': self.attributes_dictionary('duration'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
            'mw_motzois': self.attributes_dictionary('motzoi'),

            'mw_frequencies_12': self.attributes_dictionary('f12'),
            'mw_ef_amp180': self.attributes_dictionary('ef_amp180'),
            
            'ro_opt_frequency': self.attributes_dictionary('readout_opt'),
            'ro_opt_amplitude': self.attributes_dictionary('pulse_amp'),
            'pulse_durations': self.attributes_dictionary('pulse_duration'),
            'acquisition_delays': self.attributes_dictionary('acq_delay'),
            'integration_times': self.attributes_dictionary('integration_time'),
            'ro_ports': self.attributes_dictionary('readout_port'),

            'coupler': self.coupler,
        }

    def schedule_function(
        self,
        qubits : list[str],
        mw_frequencies: dict[str,float],
        mw_amplitudes: dict[str,float],
        mw_motzois: dict[str,float],
        mw_frequencies_12:  dict[str,float],
        mw_ef_amp180: dict[str,float],
        mw_pulse_durations: dict[str,float],
        mw_pulse_ports: dict[str,str],
        pulse_durations: dict[str,float],
        acquisition_delays: dict[str,float],
        integration_times: dict[str,float],
        ro_ports: dict[str,str],        
        ro_opt_frequency: dict[str,float],
        ro_opt_amplitude: dict[str,float],
        coupler: str,
        ramsey_phases: dict[str,np.ndarray],
        control_ons: dict[str,np.ndarray],
        repetitions: int = 3000,
        opt_cz_pulse_frequency: dict[str,float] = None,
        opt_cz_pulse_duration: dict[str,float] = None,
        opt_cz_pulse_amplitude: dict[str,float] = None,
        ) -> Schedule:

        dynamic = False
        if dynamic:
            name = 'CZ_dynamic_phase_ssro'
        else:
            name = 'CZ_calibration_ssro'
        schedule = Schedule(f"{name}")

        all_couplers = [coupler]
        all_qubits = [coupler.split(sep='_') for coupler in all_couplers]
        # target,control = np.transpose(qubits)[0],np.transpose(qubits)[1]
        all_qubits =  sum(all_qubits, [])
        # print(f'{target = }')
        # print(f'{control = }')

        # find cz parameters from redis
        redis_connection = redis.Redis(decode_responses=True)
        cz_pulse_frequency,cz_pulse_duration,cz_pulse_amplitude = {},{},{}
        for coupler in all_couplers:
            qubits = coupler.split(sep='_')
            for this_coupler in all_couplers:
                redis_config = redis_connection.hgetall(f"couplers:{this_coupler}")
                cz_pulse_frequency[this_coupler] = float(redis_config['cz_pulse_frequency'])
                cz_pulse_duration[this_coupler] = float(redis_config['cz_pulse_duration'])
                cz_pulse_amplitude[this_coupler] = float(redis_config['cz_pulse_amplitude'])

        for this_coupler in all_couplers:
            if opt_cz_pulse_amplitude is not None:
                cz_pulse_amplitude[this_coupler] += opt_cz_pulse_amplitude[this_coupler]
            if opt_cz_pulse_duration is not None:
                cz_pulse_duration[this_coupler] += opt_cz_pulse_duration[this_coupler]
            if opt_cz_pulse_frequency is not None:
                cz_pulse_frequency[this_coupler] += opt_cz_pulse_frequency[this_coupler]

        print(f'{cz_pulse_frequency = }')
        print(f'{cz_pulse_duration = }')
        print(f'{cz_pulse_amplitude = }')

        # The outer for-loop iterates over all qubits:
        shot = Schedule(f"shot")
        shot.add(IdlePulse(16e-9))
        
        #Initialize ClockResource with the first frequency value
        for this_qubit, ro_array_val in ro_opt_frequency.items():
            schedule.add_resource( ClockResource(name=f'{this_qubit}.ro_opt', freq=ro_array_val) )
        for this_qubit, mw_f_val in mw_frequencies.items():
            schedule.add_resource(ClockResource( name=f'{this_qubit}.01', freq=mw_f_val))
        for this_qubit, ef_f_val in mw_frequencies_12.items():
            schedule.add_resource(ClockResource(name=f'{this_qubit}.12', freq=ef_f_val))
        for index, this_coupler in enumerate(all_couplers):
            schedule.add_resource(ClockResource(name=f'{this_coupler}.cz', freq=-cz_pulse_frequency[this_coupler]+4.4e9))
            shot.add_resource(ClockResource(name=f'{this_coupler}.cz', freq=-cz_pulse_frequency[this_coupler]+4.4e9))
        # print(ramsey_phases,qubits)
        # schedule.add_resource(ClockResource(name='q11_q12.cz', freq=-cz_pulse_frequency[this_coupler]+4.4e9))
        # shot.add_resource(ClockResource(name='q11_q12.cz', freq=-cz_pulse_frequency[this_coupler]+4.4e9))

        ramsey_phases_values = ramsey_phases[all_qubits[0]]
        number_of_phases = len(ramsey_phases_values)+3 # +3 for calibration points
        control_on_values = control_ons[all_qubits[0]]

        for cz_index,control_on in enumerate(control_on_values):
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
                            if qubit_types[this_qubit] == 'Control':
                                x = shot.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                        
                for this_qubit in all_qubits:
                    if qubit_types[this_qubit] == 'Target':
                        x90 = shot.add(X90(this_qubit), ref_op=relaxation, ref_pt='end')
                
                buffer_start = shot.add(IdlePulse(4e-9), ref_op=x90, ref_pt='end')
                for this_coupler in all_couplers:
                    cz_clock = f'{this_coupler}.cz'
                    cz_pulse_port = f'{this_coupler}:fl'
                    # cz_clock = 'q11_q12.cz'
                    # cz_pulse_port = 'q11_q12:fl'
                    reset_phase = shot.add(ResetClockPhase(clock=cz_clock),
                            ref_op=buffer_start, ref_pt='end',)
                    cz = shot.add(
                            SoftSquarePulse(
                                duration = cz_pulse_duration[this_coupler],
                                amp = cz_pulse_amplitude[this_coupler],
                                port = cz_pulse_port,
                                clock = cz_clock,
                                # port = 'q11_q12:fl',
                                # clock = 'q11_q12.cz',
                            )
                        )
                    # cz = shot.add(IdlePulse(cz_pulse_duration[this_coupler]))
                buffer_end = shot.add(IdlePulse(4e-9),ref_op=buffer_start, ref_pt='end',rel_time = np.ceil( cz_pulse_duration[this_coupler] * 1e9 / 4) * 4e-9)
                if not dynamic:
                    if control_on:
                        for this_qubit in all_qubits:
                            if qubit_types[this_qubit] == 'Control':
                                x_end = shot.add(X(this_qubit), ref_op=buffer_end, ref_pt='end')
                                # x_end = shot.add(IdlePulse(20e-9))
                        
                for this_qubit in all_qubits:
                    if qubit_types[this_qubit] == 'Target':
                        x90_end = shot.add(Rxy(theta=90, phi=ramsey_phase, qubit=this_qubit), ref_op=buffer_end, ref_pt='end')
                
                for this_qubit in all_qubits:
                    this_index = cz_index*number_of_phases+ramsey_index
                    # print(f'{this_index = }')
                    shot.add(Measure_RO_Opt(this_qubit, acq_index=this_index, bin_mode=BinMode.APPEND),
                                    ref_op=x90_end, ref_pt="end",)

            # Calibration points
            root_relaxation = shot.add(Reset(*all_qubits), label=f"Reset_Calib_{cz_index}")
            
            for this_qubit in all_qubits:
                qubit_levels = range(self.qubit_state+1)
                number_of_levels = len(qubit_levels)

                shot.add(Reset(*all_qubits), ref_op=root_relaxation, ref_pt_new='end') #To enforce parallelism we refer to the root relaxation
                # The intermediate for-loop iterates over all ro_amplitudes:
                # for ampl_indx, ro_amplitude in enumerate(ro_amplitude_values):
                # The inner for-loop iterates over all qubit levels:
                for level_index, state_level in enumerate(qubit_levels):
                    calib_index = this_index + level_index + 1
                    # print(f'{calib_index = }')
                    if state_level == 0:
                        prep = shot.add(IdlePulse(mw_pulse_durations[this_qubit]))
                    elif state_level == 1:
                        prep = shot.add(X(this_qubit),)
                    elif state_level == 2:
                        shot.add(X(this_qubit),)
                        prep = shot.add(Rxy_12(this_qubit),)
                    else:
                        raise ValueError('State Input Error')
                    shot.add(Measure_RO_Opt(this_qubit, acq_index=calib_index, bin_mode=BinMode.APPEND),
                                    ref_op=prep, ref_pt="end",)
                    shot.add(Reset(this_qubit))
        shot.add(IdlePulse(16e-9))

        schedule.add(IdlePulse(16e-9))
        schedule.add(shot, control_flow=Loop(repetitions), validate=False)
        # for rep in range(10):
        #     schedule.add(shot, validate=False)
        schedule.add(IdlePulse(16e-9))

        return schedule
