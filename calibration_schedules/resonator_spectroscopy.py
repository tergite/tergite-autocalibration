from quantify_scheduler.enums import BinMode
from quantify_scheduler.schedules.schedule import Schedule
from quantify_scheduler.operations.pulse_library import  SquarePulse, SetClockFrequency, DRAGPulse
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.operations.gate_library import Reset, X, Measure
from quantify_scheduler.resources import ClockResource
from transmon_element import Measure_1

from measurement_base import Measurement

class Resonator_Spectroscopy(Measurement):

    def __init__(self,transmons,connections,qubit_state:int=0):
        super().__init__(transmons,connections)
        self.experiment_parameters = ['ro_freq_NCO']
        self.qubit_state = qubit_state
        self.gettable_batched = True
        self.transmons = transmons

        self.static_kwargs = {
            'pulse_amplitudes': self.attributes_dictionary('ro_pulse_amp'),
            'pulse_durations' : self.attributes_dictionary('ro_pulse_duration'),
            'acquisition_delays': self.attributes_dictionary('ro_acq_delay'),
            'integration_times': self.attributes_dictionary('ro_acq_integration_time'),
            'mw_ef_amp180s': self.attributes_dictionary('mw_ef_amp180'),
            'mw_pulse_durations': self.attributes_dictionary('mw_pulse_duration'),
            'mw_clocks_12': self.attributes_dictionary('mw_12_clock'),
            'mw_pulse_ports': self.attributes_dictionary('mw_port'),
            'freqs_12': self.attributes_dictionary('freq_12'),
            'qubits': self.qubits,
            'ports': self.attributes_dictionary('ro_port'),
            'clocks': self.attributes_dictionary('ro_clock'),
            'clocks_1': self.attributes_dictionary('ro_clock_1'),
            'clocks_2': self.attributes_dictionary('ro_clock_2'),
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
        return self._settables_dictionary(parameters, isBatched=self.gettable_batched, mp_data=mp_data)

    def setpoints_array(self):
        return self._setpoints_1d_array()

    def schedule_function(
            self,
            pulse_amplitudes: dict[str,float],
            pulse_durations: dict[str,float],
            mw_ef_amp180s: dict[str,float],
            mw_pulse_durations: dict[str,float],
            mw_clocks_12: dict[str,str],
            mw_pulse_ports: dict[str,str],
            freqs_12:  dict[str,float],
            acquisition_delays: dict[str,float],
            integration_times: dict[str,float],
            qubits: list[str],
            ports: dict[str,str],
            clocks: dict[str,str],
            clocks_1: dict[str,str],
            clocks_2: dict[str,str],
            repetitions: int = 1024,

            **ro_frequencies
        ) -> Schedule:

        # if port_out is None: port_out = port
        sched = Schedule("multiplexed_resonator_spec_NCO",repetitions)
        # Initialize the clock for each qubit
        for ro_key, ro_array_val in ro_frequencies.items():
            this_qubit = [qubit for qubit in qubits if qubit in ro_key][0]
            if self.qubit_state==0:
                this_clock = clocks[this_qubit]
            elif self.qubit_state==1:
                this_clock = clocks_1[this_qubit]
            elif self.qubit_state==2:
                this_clock = clocks_2[this_qubit]

            #Initialize ClockResource with the first frequency value
            sched.add_resource( ClockResource(name=this_clock, freq=ro_array_val[0]) )

        if self.qubit_state == 2:
            for this_qubit, ef_f_val in freqs_12.items():
                sched.add_resource( ClockResource( name=mw_clocks_12[this_qubit], freq=ef_f_val) )

        root_relaxation = sched.add(Reset(*qubits), label="Reset")

        # The first for loop iterates over all qubits:
        for acq_cha, (ro_f_key, ro_f_values) in enumerate(ro_frequencies.items()):
            this_qubit = [qubit for qubit in qubits if qubit in ro_f_key][0]
            if self.qubit_state==0:
                this_clock = clocks[this_qubit]
            elif self.qubit_state==1:
                this_clock = clocks_1[this_qubit]
            elif self.qubit_state==2:
                this_clock = clocks_2[this_qubit]
            # The second for loop iterates over all frequency values in the frequency batch:
            relaxation = root_relaxation
            for acq_index, ro_frequency in enumerate(ro_f_values):
                set_frequency = sched.add(
                    SetClockFrequency(clock=this_clock, clock_freq_new=ro_frequency),
                    label=f"set_freq_{this_qubit}_{acq_index}",
                    ref_op=relaxation, ref_pt='end'
                )

                if self.qubit_state == 0:
                    excitation_pulse = set_frequency
                elif self.qubit_state == 1:
                    excitation_pulse = sched.add(X(this_qubit), ref_op=set_frequency, ref_pt='end')
                elif self.qubit_state == 2:
                    excitation_pulse_1 = sched.add(X(this_qubit), ref_op=set_frequency, ref_pt='end')
                    excitation_pulse = sched.add(
                        DRAGPulse(
                            duration=mw_pulse_durations[this_qubit],
                            G_amp=mw_ef_amp180s[this_qubit],
                            D_amp=0,
                            port=mw_pulse_ports[this_qubit],
                            clock=mw_clocks_12[this_qubit],
                            phase=0,
                        ),
                        label=f"rabi_pulse_{this_qubit}_{acq_index}", ref_op=excitation_pulse_1, ref_pt="end",
                    )

                pulse = sched.add(
                    SquarePulse(
                        duration=pulse_durations[this_qubit],
                        amp=pulse_amplitudes[this_qubit],
                        port=ports[this_qubit],
                        clock=this_clock,
                    ),
                    label=f"spec_pulse_{this_qubit}_{acq_index}", ref_op=excitation_pulse, ref_pt="end",
                )

                sched.add(
                    SSBIntegrationComplex(
                        duration=integration_times[this_qubit],
                        port=ports[this_qubit],
                        clock=this_clock,
                        acq_index=acq_index,
                        acq_channel=acq_cha,
                        bin_mode=BinMode.AVERAGE
                    ),
                    ref_op=pulse, ref_pt="start",
                    rel_time=acquisition_delays[this_qubit],
                    label=f"acquisition_{this_qubit}_{acq_index}",
                )

                #sched.add(
                #    Measure(this_qubit, acq_index=acq_index, acq_channel=acq_cha, bin_mode=BinMode.AVERAGE),
                #    label=f'Measurement_{this_qubit}_{acq_index}',
                #    ref_op=excitation_pulse,
                #    ref_pt="end",
                #)

                # update the relaxation for the next batch point
                relaxation = sched.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{acq_index}")

        return sched
