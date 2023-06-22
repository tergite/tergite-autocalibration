import numpy as np
from quantify_scheduler.operations.gate_library import Reset, X, Rxy
from quantify_scheduler.operations.pulse_library import SquarePulse, SetClockFrequency
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.schedules.schedule import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.resources import ClockResource
from measurements_base import Measurement_base
from typing import List

class SSRO_BATCHED(Measurement_base):

    def __init__(self,transmons,connections):
        super().__init__(transmons,connections)
        #order matters,
        self.experiment_parameters = ['ro_freq_NCO','ro_pulse_amp_cus','state_level']
        #Measurement control runs batched parameters in the inner loop:
        self.parameter_order = ['state_level','ro_freq_NCO','ro_pulse_amp_cus']
        self.gettable_batched = True
        self.gettable_real_imag = True
        self.static_kwargs = {
            'qubits': self.qubits,
            'pulse_durations' : self._get_attributes('ro_pulse_duration'),
            'acquisition_delays': self._get_attributes('ro_acq_delay'),
            'integration_times': self._get_attributes('ro_acq_integration_time'),
            'ports': self._get_attributes('ro_port'),
            'clocks': self._get_attributes('ro_clock'),
            'freqs_12': self._get_attributes('freq_12'),
            'mw_clocks_12': self._get_attributes('mw_12_clock'),
            'mw_ef_amp180s': self._get_attributes('mw_ef_amp180'),
            'mw_pulse_durations': self._get_attributes('mw_pulse_duration'),
            'mw_pulse_ports': self._get_attributes('mw_port'),
        }

    def settables_dictionary(self):
        parameters = self.experiment_parameters
        manual_parameter = 'state_level'
        assert( manual_parameter in self.experiment_parameters )
        mp_data = {
            manual_parameter : {
                'name': manual_parameter,
                'initial_value': 0,
                'unit': '-',
                'batched': True
            }
        }
        manual_parameter = 'ro_freq_NCO'
        assert( manual_parameter in self.experiment_parameters )
        mp_data.update( {
            manual_parameter : {
                'name': manual_parameter,
                'initial_value': 2e9,
                'unit': 'Hz',
                'batched': True
            }
        })
        manual_parameter = 'ro_pulse_amp_cus'
        assert( manual_parameter in self.experiment_parameters )
        mp_data.update( {
            manual_parameter : {
                'name': manual_parameter,
                'initial_value':1e-4,
                'unit': 'Amp',
                'batched': False
            }
        })
        return self._settables_dictionary(parameters, isBatched=self.gettable_batched, mp_data=mp_data)

    def setpoints_array(self):
        return self._setpoints_Nd_array()

    def schedule_function(
            self,
            acquisition_delays: dict[str,float],
            integration_times: dict[str,float],
            pulse_durations: dict[str,float],
            mw_ef_amp180s: dict[str,float],
            mw_clocks_12: dict[str,str],
            mw_pulse_durations: dict[str,float],
            mw_pulse_ports: dict[str,str],
            freqs_12:  dict[str,float],
            ports: dict[str,str],
            clocks: dict[str,str],
            qubits : List[str],
            repetitions: int = 1,
            **ro_optimizations
        ) -> Schedule:
        repetitions = 1 # TODO Remove Hardcoding
        schedule = Schedule("State_discrimination_schedule", repetitions)
        # print(f'{ repetitions = }')
        number_states = self.dimensions['state_level']
        number_freqs = self.dimensions['ro_freq_NCO']

        qubit_ro_params_dict = {q: {} for q in qubits}

        # Add the clock for the |1> -> |2> pulse
        for this_qubit, ef_f_val in freqs_12.items():
            schedule.add_resource( ClockResource(name=mw_clocks_12[this_qubit], freq=ef_f_val) )

        for ro_key, ro_val in ro_optimizations.items():
            this_qubit = [q for q in qubits if q in ro_key][0]
            if 'ro_freq' in ro_key :
                ro_val = ro_val.reshape(number_states,number_freqs)
                qubit_ro_params_dict[this_qubit]['ro_freq_values'] = ro_val #we expect an array
                print( 'RO_FREQUENCIES')
                print(f'{ ro_val.shape = }')
                print(f'{ ro_val = }')
                # Add the RO clock and initialize it with the first ro_val
                schedule.add_resource( ClockResource(name=clocks[this_qubit], freq=ro_val[0]) )
            if 'ro_pulse_amp' in ro_key :
                qubit_ro_params_dict[this_qubit]['ro_pulse_amp'] = ro_val
                print( 'AMPLS')
                print(f'{ ro_val.shape = }')
                print(f'{ ro_val = }')
            if 'state_level' in ro_key :
                ro_val = ro_val.reshape(number_states,number_freqs)
                qubit_ro_params_dict[this_qubit]['state_level'] = ro_val
                print( 'STATES')
                print(f'{ ro_val.shape = }')
                print(f'{ ro_val = }')

        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # print(f'{ ro_pulse_amplitude = }')
        # print(f'{ ro_frequencies = }')
        # print(f'{ rng_state_levels = }')

        # The first for-loop iterates over all qubits:
        for acq_cha, (this_qubit, ro_values) in enumerate(qubit_ro_params_dict.items()):
            ro_pulse_amplitude = ro_values['ro_pulse_amp']
            rng_state_levels = ro_values['state_level']
            rng_states_length = len(rng_state_levels)
            ro_frequencies = ro_values['ro_freq_values']

            # The second for-loop iterates over all frequency values in the frequency batch:
            relaxation = root_relaxation
            for acq_index, ro_frequency in enumerate(ro_frequencies):
                set_frequency = schedule.add(
                    SetClockFrequency(clock=clocks[this_qubit], clock_freq_new=ro_frequency),
                    label=f"set_freq_{this_qubit}_{acq_index}",
                    ref_op=relaxation, ref_pt='end'
                )

                # The third for-loop iterates over all rng levels:
                rng_root = set_frequency
                for rng_index, state_level in enumerate(rng_state_levels):
                    state_level = int(state_level+1e-2)
                    if state_level == 0:
                        shot_operation = schedule.add(
                            Rxy(theta=0, phi=0, qubit=this_qubit),
                            # label=f"RXY_{this_qubit}_{rng_index}",
                            ref_op=rng_root,
                            ref_pt='end'
                        )
                    elif state_level == 1:
                        shot_operation = schedule.add(
                            X(qubit=this_qubit), ref_op=rng_root, ref_pt='end'
                            #Rxy(theta=180, phi=0, qubit=this_qubit),
                            #label=f"RXY_{this_qubit}_{acq_ind}",
                            # the first relaxation is the root relaxation
                        )
                    elif state_level == 2:
                        initial_shot_operation = schedule.add(
                            X(qubit=this_qubit), ref_op=rng_root, ref_pt='end'
                            #Rxy(theta=180, phi=0, qubit=this_qubit),
                            #label=f"RXY_{this_qubit}_{acq_ind}",
                            ## the first relaxation is the root relaxation
                            #ref_op=relaxation,
                            #ref_pt='end'
                        )
                        shot_operation = schedule.add(
                            #TODO DRAG optimize for 1 <-> 2
                            DRAGPulse(
                                duration=mw_pulse_durations[this_qubit],
                                G_amp=mw_ef_amp180s[this_qubit],
                                D_amp=0,
                                port=mw_pulse_ports[this_qubit],
                                clock=mw_clocks_12[this_qubit],
                                phase=0,
                            ),
                            # label=f"RXY_12_{this_qubit}_{acq_index}",
                            # the first relaxation is the root relaxation
                            ref_op=initial_shot_operation,
                            ref_pt='end'
                        )
                    else:
                        print('State Input Error')

                    ro_pulse = schedule.add(
                        SquarePulse(
                            duration=pulse_durations[this_qubit],
                            amp=ro_pulse_amplitude,
                            port=ports[this_qubit],
                            clock=clocks[this_qubit],
                        ),
                        # label=f"ro_pulse_{this_qubit}_{acq_index}", ref_op=shot_operation, ref_pt="end",
                    )
                    current_index = acq_index*rng_states_length + rng_index
                    # print(f'{ current_index = }')
                    schedule.add(
                        SSBIntegrationComplex(
                            duration=integration_times[this_qubit],
                            port=ports[this_qubit],
                            clock=clocks[this_qubit],
                            acq_channel=acq_cha,
                            acq_index=current_index,
                        ),
                        ref_op=ro_pulse, ref_pt="start",
                        rel_time=acquisition_delays[this_qubit],
                        label=f"acquisition_{this_qubit}_{current_index}",
                    )

                    rng_root = schedule.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{current_index}")

        return schedule
