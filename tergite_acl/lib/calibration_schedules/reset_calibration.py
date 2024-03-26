"""
Module containing a schedule class for Ramsey calibration. (1D parameter sweep, for 2D see ramsey_detunings.py)
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X, CZ
from quantify_scheduler.operations.pulse_library import GaussPulse,RampPulse,ResetClockPhase,DRAGPulse,SetClockFrequency,NumericalPulse,SoftSquarePulse,SquarePulse,IdlePulse
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.resources import ClockResource
from tergite_acl.lib.measurement_base import Measurement
from tergite_acl.utils.extended_transmon_element import Measure_RO1, Measure_RO_Opt, Rxy_12
from quantify_scheduler.operations.control_flow_library import Loop
from tergite_acl.config.coupler_config import edge_group, qubit_types
from scipy import signal
from matplotlib import pyplot as plt
import numpy as np
import itertools

import redis

class Reset_calibration_SSRO(Measurement):

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
        repetitions: int = 4096,
        opt_reset_duration_qc: dict[str,float] = None,
        opt_reset_amplitude_qc: dict[str,float] = None,
        ) -> Schedule:

        name = 'Reset_calibration_ssro'
        schedule = Schedule(f"{name}")

        all_couplers = [coupler]
        all_qubits = [coupler.split(sep='_') for coupler in all_couplers]
        # target,control = np.transpose(qubits)[0],np.transpose(qubits)[1]
        all_qubits =  sum(all_qubits, [])
        # print(f'{target = }')
        # print(f'{control = }')


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
            if this_coupler in ['q16_q21','q17_q22','q18_q23','q19_q24']:
                downconvert = 0
            else:
                downconvert = 4.4e9
            schedule.add_resource(ClockResource(name=f'{this_coupler}.cz', freq=0+downconvert))
            shot.add_resource(ClockResource(name=f'{this_coupler}.cz', freq=0+downconvert))
        # print(ramsey_phases,qubits)
        # schedule.add_resource(ClockResource(name='q11_q12.cz', freq=-cz_pulse_frequency[this_coupler]+4.4e9))
        # shot.add_resource(ClockResource(name='q11_q12.cz', freq=-cz_pulse_frequency[this_coupler]+4.4e9))
        
        # reset_duration_qc = 704e-09
        # reset_amplitude_qc = 9.5e-2

        reset_duration_qc = 904e-09
        reset_amplitude_qc = 9.5e-2+0.013

        reset_duration_cr = 904e-09
        reset_amplitude_cr = -8.75e-2

        for this_coupler in all_couplers:
            if opt_reset_amplitude_qc is not None:
                reset_amplitude_qc += opt_reset_amplitude_qc[this_coupler]
            if opt_reset_duration_qc is not None:
                reset_duration_qc += opt_reset_duration_qc[this_coupler]

        print(f'{reset_duration_qc = }')
        print(f'{reset_amplitude_qc = }')

        ramsey_phases_values = ramsey_phases[all_qubits[0]]
        number_of_phases = len(ramsey_phases_values)+3 # +3 for calibration points
        control_on_values = control_ons[all_qubits[0]]

        # all_qubits = ['q16','q21']
        state = ['g','e','f']
        states =list(itertools.product(state, state))
        test_states = [dict(zip(all_qubits, s)) for s in states]

        for cz_index,control_on in enumerate(control_on_values):
            for ramsey_index, ramsey_phase in enumerate(ramsey_phases_values): 
                relaxation = shot.add(Reset(*all_qubits), label=f"Reset_{cz_index}_{ramsey_index}")

                test_state = test_states[int(ramsey_phase)]
                # print(f'{test_state = }')
                for this_qubit in all_qubits:
                    if test_state[this_qubit] == 'g':
                        shot.add(IdlePulse(32e-9), ref_op=relaxation, ref_pt='end')
                    elif test_state[this_qubit] == 'e':
                        shot.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                    elif test_state[this_qubit] == 'f':
                        shot.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                        shot.add(Rxy_12(this_qubit))

                reset_duration_wait = 1500e-09

                # reset_duration_qc = 460e-09
                # reset_amplitude_qc = 0.04526315789473684

                # reset_duration_cr = 350e-09
                # reset_amplitude_cr = -0.13815789473684212

                # reset_duration_qc = 560e-09
                # reset_amplitude_qc = 4.842105263157895e-2

                # reset_duration_cr = 400e-09
                # reset_amplitude_cr = -14.473684210526317e-2

                rep = 1
                    
                buffer = shot.add(IdlePulse(4e-9))

                if control_on:

                    cz_clock = f'{this_coupler}.cz'
                    cz_pulse_port = f'{this_coupler}:fl'

                    start = shot.add(ResetClockPhase(clock=coupler+'.cz'))
                    
                    # buffer = shot.add(IdlePulse(20e-9),ref_op=buffer, ref_pt='end')
                    for this_qubit in qubits:
                    # schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                        if qubit_types[this_qubit] == 'Target':
                            # shot.add(IdlePulse(32e-9), ref_op=start, ref_pt='end')
                            # schedule.add(IdlePulse(20e-9))
                            # schedule.add(X(this_qubit))
                            shot.add(Rxy_12(this_qubit,theta = 90), ref_op=start, ref_pt='end')
                        else:
                            # schedule.add(X(this_qubit), ref_op=start, ref_pt='end')
                            # schedule.add(Rxy_12(this_qubit))
                            # schedule.add(IdlePulse(20e-9))
                            shot.add(IdlePulse(32e-9), ref_op=start, ref_pt='end')
                    
                    buffer = shot.add(IdlePulse(4e-9))

                    for i in range(rep):
                        qc = shot.add(
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

                        buffer = shot.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc * 1e9 / 4) * 4e-9)
                        # buffer = shot.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)

                        cr = shot.add(
                                    RampPulse(
                                        duration = reset_duration_cr,
                                        offset = reset_amplitude_cr,
                                        amp = -reset_amplitude_cr/11,
                                        # duration = reset_duration,
                                        # offset = reset_amplitude,
                                        # amp = -reset_amplitude/11,
                                        port = cz_pulse_port,
                                        clock = cz_clock,
                                    ),
                                )

                        buffer = shot.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr * 1e9 / 4) * 4e-9)
                        
                        # qc = shot.add(
                        #         RampPulse(
                        #             # offset = reset_amplitude/1.5,
                        #             # duration = reset_duration,
                        #             # amp = reset_amplitude,
                        #             duration = reset_duration_qc,
                        #             offset = reset_amplitude_qc/1.5,
                        #             amp = reset_amplitude_qc,
                        #             # amp = 0,
                        #             port = cz_pulse_port,
                        #             clock = cz_clock,
                        #         ),
                        #     )

                        # buffer = shot.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc * 1e9 / 4) * 4e-9)
                        # buffer = shot.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)

                        if rep > 1 and i < rep-1:
                            buffer = shot.add(IdlePulse(np.ceil( reset_duration_wait * 1e9 / 4) * 4e-9),ref_op=buffer, ref_pt='end')
                    
                    # for this_qubit in qubits:
                    # # schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                    #     if qubit_types[this_qubit] == 'Target':
                    #         # schedule.add(IdlePulse(20e-9), ref_op=relaxation, ref_pt='end')
                    #         # schedule.add(IdlePulse(20e-9))
                    #         # schedule.add(X(this_qubit))
                    #         shot.add(Rxy(this_qubit,theta = 10), ref_op=start, ref_pt='end')
                    #     else:
                    #         # schedule.add(X(this_qubit), ref_op=start, ref_pt='end')
                    #         # schedule.add(Rxy_12(this_qubit))
                    #         # schedule.add(IdlePulse(20e-9))
                    #         shot.add(IdlePulse(20e-9), ref_op=start, ref_pt='end')

                        
                # else:
                        # buffer = shot.add(IdlePulse(np.ceil( (reset_duration_qc+reset_duration_cr+reset_duration_wait) * rep * 1e9 / 4) * 4e-9),ref_op=buffer, ref_pt='end')

################################################################################################

                    # reset_duration_qc = 20e-09
                    # reset_amplitude_qc = -0.025

                    # reset_duration_qc_gf = 25e-09
                    # reset_amplitude_qc_gf = -0.044

                    # reset_duration_cr = 190e-09
                    # reset_amplitude_cr = 0.055

                    # reset_duration_cr_gf = 360e-09
                    # reset_amplitude_cr_gf = 0.061

                    # reset_duration_qc_fg = 15e-09
                    # reset_amplitude_qc_fg = -0.076

                    # reset_duration_qc_ad = 2000e-9
                    # reset_amplitude_qc_ad = -0.04

                    # buffer = shot.add(IdlePulse(4e-9))

                    # qc = shot.add(
                    #         RampPulse(
                    #             duration = reset_duration_qc_ad,
                    #             offset = reset_amplitude_qc_ad,
                    #             amp = - reset_amplitude_qc_ad,
                    #             # duration = reset_duration_qc,
                    #             # amp = 0,
                    #             port = cz_pulse_port,
                    #             clock = cz_clock,
                    #         ),
                    #     )

                    # buffer = shot.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc_ad * 1e9 / 4) * 4e-9)
                    # buffer = shot.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
               
                    # qc = shot.add(
                    #             RampPulse(
                    #                 duration = reset_duration_qc_fg,
                    #                 offset = reset_amplitude_qc_fg,
                    #                 # amp = - reset_duration / target_duration* reset_amplitude,
                    #                 amp = 0,
                    #                 port = cz_pulse_port,
                    #                 clock = cz_clock,
                    #             ),
                    #         )

                    # buffer_qc = shot.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc_fg * 1e9 / 4) * 4e-9)
                    # # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
                    
                    # qc = shot.add(
                    #             GaussPulse(
                    #                 # duration = reset_duration,
                    #                 # G_amp = reset_amplitude,
                    #                 duration = reset_duration_qc_gf,
                    #                 G_amp = reset_amplitude_qc_gf,
                    #                 phase = 0,
                    #                 port = cz_pulse_port,
                    #                 clock = cz_clock,
                    #             ),
                    #         )

                    # buffer = shot.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc_gf * 1e9 / 4) * 4e-9)
                    # buffer_qc = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
                    

                    # qc = shot.add(
                    #             GaussPulse(
                    #                 # duration = reset_duration,
                    #                 # G_amp = reset_amplitude,
                    #                 duration = reset_duration_qc,
                    #                 G_amp = reset_amplitude_qc,
                    #                 phase = 0,
                    #                 port = cz_pulse_port,
                    #                 clock = cz_clock,
                    #             ),
                    #         )

                    # buffer = shot.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc * 1e9 / 4) * 4e-9)
                    # # buffer_qc = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)

                    # cr = shot.add(
                    #             RampPulse(
                    #                 duration = reset_duration_cr,
                    #                 offset = reset_amplitude_cr,
                    #                 # duration = reset_duration,
                    #                 # offset = reset_amplitude,
                    #                 amp = 0,
                    #                 port = cz_pulse_port,
                    #                 clock = cz_clock,
                    #             ),
                    #         )

                    # buffer = shot.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr * 1e9 / 4) * 4e-9)
                    # # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
                
                    # cr = shot.add(
                    #             RampPulse(
                    #                 duration = reset_duration_cr_gf,
                    #                 offset = reset_amplitude_cr_gf,
                    #                 # duration = reset_duration,
                    #                 # offset = reset_amplitude,
                    #                 amp = 0,
                    #                 port = cz_pulse_port,
                    #                 clock = cz_clock,
                    #             ),
                    #         )

                    # buffer = shot.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr_gf * 1e9 / 4) * 4e-9)
                    # # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)
                    

                    # Adiabatic reset
                    
                    # reset_duration_qc = 65e-09
                    # reset_amplitude_qc = -0.05

                    # reset_duration_cr = 200e-09
                    # reset_amplitude_cr = 0.055

                    # reset_duration_qc_f= 15e-09
                    # reset_amplitude_qc_f = -0.076
                    
                    # reset_duration_cq = 6e-09
                    # reset_amplitude_cq = -0.017

                    # qc = shot.add(
                    #             RampPulse(
                    #                 duration = reset_duration_qc,
                    #                 offset = reset_amplitude_qc,
                    #                 amp = -reset_amplitude_qc,
                    #                 # duration = reset_duration,
                    #                 # offset = reset_amplitude,
                    #                 # amp = -reset_amplitude,
                    #                 # amp = 0,
                    #                 port = cz_pulse_port,
                    #                 clock = cz_clock,
                    #             ),
                    #         )

                    # buffer_qc = shot.add(IdlePulse(4e-9),ref_op=buffer_start, ref_pt='end',rel_time = np.ceil( reset_duration_qc * 1e9 / 4) * 4e-9)

                    # cr = shot.add(
                    #             RampPulse(
                    #                 # duration = reset_duration,
                    #                 # offset = reset_amplitude,
                    #                 duration = reset_duration_cr,
                    #                 offset = reset_amplitude_cr,
                    #                 amp = 0,
                    #                 port = cz_pulse_port,
                    #                 clock = cz_clock,
                    #             ),
                    #         )

                    # buffer_cr = shot.add(IdlePulse(4e-9),ref_op=buffer_qc, ref_pt='end',rel_time = np.ceil( reset_duration_cr * 1e9 / 4) * 4e-9)

                    # qc = shot.add(
                    #             RampPulse(
                    #                 duration = reset_duration_qc_f,
                    #                 offset = reset_amplitude_qc_f,
                    #                 amp = 0,
                    #                 port = cz_pulse_port,
                    #                 clock = cz_clock,
                    #             ),
                    #         )

                            
                    # buffer_qc = shot.add(IdlePulse(4e-9),ref_op=buffer_cr, ref_pt='end',rel_time = np.ceil( reset_duration_qc_f * 1e9 / 4) * 4e-9)

                    # cr = shot.add(
                    #             RampPulse(
                    #                 # duration = reset_duration,
                    #                 # offset = reset_amplitude,
                    #                 duration = reset_duration_cr,
                    #                 offset = reset_amplitude_cr,
                    #                 amp = 0,
                    #                 port = cz_pulse_port,
                    #                 clock = cz_clock,
                    #             ),
                    #         )
                    # buffer_cr = shot.add(IdlePulse(4e-9),ref_op=buffer_qc, ref_pt='end',rel_time = np.ceil( reset_duration_cr * 1e9 / 4) * 4e-9)

                buffer_end = shot.add(IdlePulse(20e-9))

                for this_qubit in all_qubits:
                    this_index = cz_index*number_of_phases+ramsey_index
                    # print(f'{this_index = }')
                    shot.add(Measure_RO_Opt(this_qubit, acq_index=this_index, bin_mode=BinMode.APPEND),
                                    ref_op=buffer_end, ref_pt="end",)

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
