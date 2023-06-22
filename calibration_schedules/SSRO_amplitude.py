from quantify_scheduler.resources import ClockResource
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse, SquarePulse
from quantify_scheduler.operations.gate_library import Reset, X, Rxy
from measurements_base import Measurement_base
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex

class SSRO_amplitude_BATCHED(Measurement_base):

    def __init__(self,transmons,connections):
        super().__init__(transmons,connections)
        self.experiment_parameters = ['ro_ampl_BATCHED', 'state_level'] # The order maters
        self.parameter_order = ['ro_ampl_BATCHED', 'state_level'] # The order maters
        self.gettable_batched = True
        self.static_kwargs = {
            'qubits': self.qubits,
            'pulse_durations' : self._get_attributes('ro_pulse_duration'),
            'acquisition_delays': self._get_attributes('ro_acq_delay'),
            'integration_times': self._get_attributes('ro_acq_integration_time'),
            'ports': self._get_attributes('ro_port'),
            'ro_clocks': self._get_attributes('ro_clock'),
            'ro_freqs': self._get_attributes('ro_freq'),
            'freqs_12': self._get_attributes('freq_12'),
            'mw_clocks_12': self._get_attributes('mw_12_clock'),
            'mw_ef_amp180s': self._get_attributes('mw_ef_amp180'),
            'mw_pulse_durations': self._get_attributes('mw_pulse_duration'),
            'mw_pulse_ports': self._get_attributes('mw_port'),
        }

    def settables_dictionary(self):
        parameters = self.experiment_parameters
        manual_parameter = 'ro_ampl_BATCHED'
        assert( manual_parameter in self.experiment_parameters )
        mp_data = {
            manual_parameter : {
                'name': manual_parameter,
                'initial_value': 1e-4,
                'unit': 'V',
                'batched': False
            }
        }
        manual_parameter = 'state_level'
        assert( manual_parameter in self.experiment_parameters )
        mp_data.update( {
            manual_parameter: {
                'name': manual_parameter,
                'initial_value': 0,
                'unit': '-',
                'batched': True
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
            ro_freqs:  dict[str,float],
            ports: dict[str,str],
            ro_clocks: dict[str,str],
            qubits : List[str],
            repetitions: int = 1,
            **ro_optimizations
        ) -> Schedule:
        repetitions = 1 # TODO Remove Hardcoding
        schedule = Schedule("State_discrimination_schedule", repetitions)

        qubit_ro_params_dict = {q: {} for q in qubits}

        # Add the clock for the |1> -> |2> pulse
        for this_qubit, ef_f_val in freqs_12.items():
            schedule.add_resource( ClockResource(name=mw_clocks_12[this_qubit], freq=ef_f_val) )
        for this_qubit, ro_freq_val in ro_freqs.items():
            schedule.add_resource( ClockResource(name=ro_clocks[this_qubit], freq=ro_freq_val) )

        for ro_key, ro_val in ro_optimizations.items():
            this_qubit = [q for q in qubits if q in ro_key][0]
            if 'ro_ampl' in ro_key :
                qubit_ro_params_dict[this_qubit]['ro_ampl_values'] = ro_val #we expect an array
                print('RO_AMPLS')
                print(f'{ ro_val = }')
                # Add the RO clock and initialize it with the first ro_val
                # schedule.add_resource( ClockResource(name=ro_clocks[this_qubit], freq=ro_val[0]) )

            if 'state_level' in ro_key :
                qubit_ro_params_dict[this_qubit]['state_level'] = ro_val

        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The first for-loop iterates over all qubits:
        for acq_cha, (this_qubit, ro_values) in enumerate(qubit_ro_params_dict.items()):
            rng_state_levels = ro_values['state_level']
            ro_amplitudes = ro_values['ro_ampl_values']

            # The second for-loop iterates over all amplitude values in the amplitude batch:
            relaxation = schedule.add(
                Reset(*qubits), label=f'Reset_{acq_cha}', ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            for acq_index, ro_ampl in enumerate(ro_amplitudes):
                # The third for-loop iterates over all rng levels:
                for rng_index, state_level in enumerate(rng_state_levels):
                    state_level = int(state_level+1e-2)
                    if state_level == 0:
                        schedule.add(
                            Rxy(theta=0, phi=0, qubit=this_qubit),
                        )
                    elif state_level == 1:
                        schedule.add(
                            X(qubit=this_qubit),
                            #Rxy(theta=180, phi=0, qubit=this_qubit),
                            #label=f"RXY_{this_qubit}_{acq_ind}",
                            # the first relaxation is the root relaxation
                        )
                    elif state_level == 2:
                        schedule.add(
                            X(qubit=this_qubit),
                            #Rxy(theta=180, phi=0, qubit=this_qubit),
                            #label=f"RXY_{this_qubit}_{acq_ind}",
                            ## the first relaxation is the root relaxation
                            #ref_op=relaxation,
                            #ref_pt='end'
                        )
                        schedule.add(
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
                        )
                    else:
                        print('State Input Error')

                    ro_pulse = schedule.add(
                        SquarePulse(
                            duration=pulse_durations[this_qubit],
                            amp=ro_ampl,
                            port=ports[this_qubit],
                            clock=ro_clocks[this_qubit],
                        ),
                        # label=f"ro_pulse_{this_qubit}_{acq_index}", ref_op=shot_operation, ref_pt="end",
                    )
                    # print(f'{ current_index = }')
                    schedule.add(
                        SSBIntegrationComplex(
                            duration=integration_times[this_qubit],
                            port=ports[this_qubit],
                            clock=ro_clocks[this_qubit],
                            acq_channel=acq_cha,
                            acq_index=rng_index,
                        ),
                        ref_op=ro_pulse, ref_pt="start",
                        rel_time=acquisition_delays[this_qubit],
                        label=f"acquisition_{this_qubit}_{rng_index}",
                    )

                    schedule.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{rng_index}")

        return schedule
