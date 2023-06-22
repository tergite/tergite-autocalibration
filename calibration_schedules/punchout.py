from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.resources import ClockResource
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import SquarePulse, SetClockFrequency
from quantify_scheduler.operations.gate_library import Reset
from measurements_base import Measurement_base


class Punchout_BATCHED(Measurement_base):

    def __init__(self,transmons,connections):
        super().__init__(transmons,connections)
        self.experiment_parameters = ['ro_freq_NCO', 'ro_ampl_BATCHED'] # The order maters
        self.parameter_order = ['ro_freq_NCO', 'ro_ampl_BATCHED'] # The order maters
        self.gettable_batched = True
        self.static_kwargs = {
            'qubits': self.qubits,
            'pulse_durations': self._get_attributes('ro_pulse_duration'),
            'acquisition_delays': self._get_attributes('ro_acq_delay'),
            'integration_times': self._get_attributes('ro_acq_integration_time'),
            'ports': self._get_attributes('ro_port'),
            'clocks': self._get_attributes('ro_clock'),
        }

    def settables_dictionary(self):
        parameters = self.experiment_parameters
        manual_parameter = 'ro_freq_NCO'
        assert( manual_parameter in self.experiment_parameters )
        mp_data = {
            manual_parameter : {
                'name': manual_parameter,
                'initial_value': 2e9,
                'unit': 'Hz',
                'batched': True
            }
        }
        manual_parameter = 'ro_ampl_BATCHED'
        assert( manual_parameter in self.experiment_parameters )
        mp_data.update( {
            manual_parameter: {
                'name': manual_parameter,
                'initial_value': 1e-4,
                'unit': 'V',
                'batched': False
            }
        })
        return self._settables_dictionary(parameters, isBatched=self.gettable_batched, mp_data=mp_data)

    def setpoints_array(self):
        return self._setpoints_Nd_array()

    def schedule_function(
            self,
            qubits: list[str],
            pulse_durations: dict[str,float],
            acquisition_delays: dict[str,float],
            integration_times: dict[str,float],
            ports: dict[str,str],
            clocks: dict[str,str],
            repetitions: int = 1024,
            **punchout_parameters,
        ) -> Schedule:
        schedule = Schedule("mltplx_punchout",repetitions)

        values = {qubit:{} for qubit in qubits}

        for punchout_key, punchout_val in punchout_parameters.items():
            this_qubit = [q for q in qubits if q in punchout_key][0]
            if 'freq' in punchout_key:
               values[this_qubit].update({'ro_freq':punchout_val})
               schedule.add_resource(
                    ClockResource(
                        name=clocks[this_qubit],
                        freq=punchout_val[0]) #Initialize ClockResource with the first frequency value
                )
            if 'ampl' in punchout_key:
               values[this_qubit].update({'ro_ampl':punchout_val})

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        for acq_cha, (values_key, values_val) in enumerate(values.items()):
            this_qubit = [q for q in qubits if q in values_key][0]
            this_clock = clocks[this_qubit]

            ro_frequencies_values = values_val['ro_freq']
            ro_amplitude = values_val['ro_ampl']

            relaxation = schedule.add(
                Reset(*qubits), label=f'Reset_{acq_cha}', ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            #The second for loop iterates over all frequency values in the frequency batch:
            for acq_index, ro_freq in enumerate(ro_frequencies_values):

                schedule.add(
                    SetClockFrequency(clock=this_clock, clock_freq_new=ro_freq),
                    label=f"set_freq_{this_qubit}_{acq_index}",
                )

                schedule.add(
                    SquarePulse(
                        duration=pulse_durations[this_qubit],
                        amp=ro_amplitude,
                        port=ports[this_qubit],
                        clock=this_clock,
                    ),
                    label=f"ro_spec_pulse_{this_qubit}_{acq_index}", ref_pt="end",
                )

                schedule.add(
                    SSBIntegrationComplex(
                        duration=integration_times[this_qubit],
                        port=ports[this_qubit],
                        clock=this_clock,
                        acq_index=acq_index,
                        acq_channel=acq_cha,
                        bin_mode=BinMode.AVERAGE
                    ),
                    ref_pt="start",
                    rel_time=acquisition_delays[this_qubit],
                    label=f"acquisition_{this_qubit}_{acq_index}",
                )

                schedule.add(Reset(this_qubit))

        return schedule
