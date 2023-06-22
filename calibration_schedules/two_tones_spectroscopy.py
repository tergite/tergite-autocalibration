from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from quantify_scheduler.operations.pulse_library import (SetClockFrequency,
                                                         SoftSquarePulse,
                                                         SquarePulse)
from quantify_scheduler.resources import ClockResource
from quantify_scheduler.schedules.schedule import Schedule

from measurements_base import Measurement_base
from transmon_element import Measure_1


class Two_Tones_Spectroscopy_NCO(Measurement_base):

    def __init__(self,transmons,connections,qubit_state:int=0):
        super().__init__(transmons,connections)
        if qubit_state == 0:
            spec_clock = 'spec_pulse_clock'
            self.experiment_parameters = 'freq_01_NCO'
        elif qubit_state == 1:
            spec_clock = 'mw_12_clock'
            self.experiment_parameters = 'freq_12_NCO'
        else:
            raise ValueError(f'Invalid qubit state: {qubit_state}')

        self.gettable_batched = True
        self.qubit_state = qubit_state
        self.static_kwargs = {
            'qubits': self.qubits,
            'spec_pulse_durations': self._get_attributes('spec_pulse_duration'),
            'spec_pulse_amps': self._get_attributes('spec_pulse_amp'),
            'spec_pulse_ports': self._get_attributes('mw_port'),
            'spec_clocks': self._get_attributes(f'{spec_clock}'),

            'ro_pulse_amplitudes': self._get_attributes('ro_pulse_amp'),
            'ro_pulse_durations' : self._get_attributes('ro_pulse_duration'),
            'ro_frequencies': self._get_attributes('ro_freq'),
            'ro_frequencies_1': self._get_attributes('ro_freq_1'),
            'integration_times': self._get_attributes('ro_acq_integration_time'),
            'acquisition_delays': self._get_attributes('ro_acq_delay'),
            'clocks': self._get_attributes('ro_clock'),
            'clocks_1': self._get_attributes('ro_clock_1'),
            'ports': self._get_attributes('ro_port'),
        }

    def settables_dictionary(self):
        if self.qubit_state == 0: manual_parameter = 'freq_01_NCO'
        elif self.qubit_state == 1: manual_parameter = 'freq_12_NCO'
        else:
            raise ValueError(f'Invalid qubit state: {self.qubit_state}')
        parameters = self.experiment_parameters
        assert( manual_parameter in self.experiment_parameters )
        mp_data = {
            manual_parameter : {
                'name': manual_parameter,
                'initial_value': 2e9,
                'unit': 'Hz',
                'batched': True
            }
        }
        return self._settables_dictionary(parameters, isBatched=self.gettable_batched, mp_data=mp_data)

    def setpoints_array(self):
        return self._setpoints_1d_array()

    def schedule_function(
            self,
            qubits: list[str],
            spec_pulse_ports: dict[str,str],
            spec_clocks: dict[str,str],
            spec_pulse_durations: dict[str,float],
            spec_pulse_amps: dict[str,float],

            ro_pulse_amplitudes: dict[str,float],
            ro_pulse_durations: dict[str,float],
            ro_frequencies: dict[str,float],
            ro_frequencies_1: dict[str,float],
            integration_times: dict[str,float],
            acquisition_delays: dict[str,float],
            clocks: dict[str,str],
            clocks_1: dict[str,str],
            ports: dict[str,str],

            repetitions: int = 1024,
            **spec_pulse_frequencies,
        ) -> Schedule:

        # if port_out is None: port_out = port
        sched = Schedule("multiplexed_qubit_spec_NCO",repetitions)
        # Initialize the clock for each qubit
        for spec_key, spec_array_val in spec_pulse_frequencies.items():
            this_qubit = [qubit for qubit in qubits if qubit in spec_key][0]

            sched.add_resource(
                ClockResource( name=spec_clocks[this_qubit], freq=spec_array_val[0]),
            )

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = sched.add(Reset(*qubits), label="Reset")

        # The first for loop iterates over all qubits:
        for acq_cha, (spec_key, spec_array_val) in enumerate(spec_pulse_frequencies.items()):
            this_qubit = [qubit for qubit in qubits if qubit in spec_key][0]
            if self.qubit_state==0:
                this_clock = clocks[this_qubit]
                this_ro_frequency = ro_frequencies[this_qubit]
            elif self.qubit_state==1:
                this_clock = clocks_1[this_qubit]
                this_ro_frequency = ro_frequencies_1[this_qubit]
            else:
                raise ValueError(f'Invalid qubit state: {self.qubit_state}')

            sched.add_resource( ClockResource(name=this_clock, freq=this_ro_frequency) )

            # The second for loop iterates over all frequency values in the frequency batch:
            relaxation = root_relaxation #To enforce parallelism we refer to the root relaxation
            for acq_index, spec_pulse_frequency in enumerate(spec_array_val):
                #reset the clock frequency for the qubit pulse
                set_frequency = sched.add(
                    SetClockFrequency(clock=spec_clocks[this_qubit], clock_freq_new=spec_pulse_frequency),
                    label=f"set_freq_{this_qubit}_{acq_index}",
                    ref_op=relaxation, ref_pt='end'
                )

                if self.qubit_state == 0:
                    excitation_pulse = set_frequency
                elif self.qubit_state == 1:
                    excitation_pulse = sched.add(X(this_qubit), ref_op=set_frequency, ref_pt='end')
                else:
                    raise ValueError(f'Invalid qubit state: {self.qubit_state}')

                #spectroscopy pulse
                spec_pulse = sched.add(
                    SoftSquarePulse(
                        duration=spec_pulse_durations[this_qubit],
                        amp=spec_pulse_amps[this_qubit],
                        port=spec_pulse_ports[this_qubit],
                        clock=spec_clocks[this_qubit],
                    ),
                    label=f"spec_pulse_{this_qubit}_{acq_index}", ref_op=excitation_pulse, ref_pt="end",
                )

                if self.qubit_state == 0:
                    measure_function = Measure
                elif self.qubit_state == 1:
                    measure_function = Measure_1

                sched.add(
                    measure_function(this_qubit, acq_channel=acq_cha, acq_index=acq_index,bin_mode=BinMode.AVERAGE),
                    ref_op=spec_pulse,
                    ref_pt='end',
                    label=f'Measurement_{this_qubit}_{acq_index}'
                )

                # print(f'{ measure_function.items(measure_function) = }')
                # print(f'{ this_clock = }')
                # print(f'{ this_ro_frequency = }')

                #ro_pulse = sched.add(
                #    SquarePulse(
                #        duration=ro_pulse_durations[this_qubit],
                #        amp=ro_pulse_amplitudes[this_qubit],
                #        port=ports[this_qubit],
                #        clock=this_clock,
                #    ),
                #    label=f"ro_pulse_{this_qubit}_{acq_index}", ref_op=spec_pulse, ref_pt="end",
                #)


                #sched.add(
                #    SSBIntegrationComplex(
                #        duration=integration_times[this_qubit],
                #        port=ports[this_qubit],
                #        clock=this_clock,
                #        acq_index=acq_index,
                #        acq_channel=acq_cha,
                #        bin_mode=BinMode.AVERAGE
                #    ),
                #    ref_op=ro_pulse, ref_pt="start",
                #    rel_time=acquisition_delays[this_qubit],
                #    label=f"acquisition_{this_qubit}_{acq_index}",
                #)


                # update the relaxation for the next batch point
                relaxation = sched.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{acq_index}")

        return sched
