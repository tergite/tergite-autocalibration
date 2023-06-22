from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.resources import ClockResource
from measurements_base import Measurement_base
from transmon_element import Measure_1
import numpy as np

class Ramsey_fringes_BATCHED(Measurement_base):

    def __init__(self,transmons,connections,qubit_state:int=0):
        super().__init__(transmons,connections)
        self.experiment_parameters = 'ramsey_delay_BATCHED'
        artificial_detuning = 3.0e6 #TODO remove hardcoding
        self.gettable_batched = True
        self.qubit_state = qubit_state
        self.static_kwargs = {
            'qubits': self.qubits,
            'artificial_detuning': artificial_detuning,

            'mw_ef_amps180': self._get_attributes('mw_ef_amp180'),
            'mw_clocks_12': self._get_attributes('mw_12_clock'),
            'mw_frequencies_12': self._get_attributes('freq_12'),
            'mw_pulse_ports': self._get_attributes('mw_port'),
            'mw_pulse_durations': self._get_attributes('mw_pulse_duration'),
        }

    def settables_dictionary(self):
        parameters = self.experiment_parameters
        manual_parameter = 'ramsey_delay_BATCHED'
        assert( manual_parameter in self.experiment_parameters )
        mp_data = {
            manual_parameter : {
                'name': manual_parameter,
                'initial_value': 12e-9,
                'unit': 's',
                'batched': True
            }
        }
        return self._settables_dictionary(parameters, isBatched=self.gettable_batched, mp_data=mp_data)

    def setpoints_array(self):
        return self._setpoints_1d_array()

    def schedule_function(
        self,
        qubits: list[str],
        mw_clocks_12: dict[str,str],
        mw_ef_amps180: dict[str,float],
        mw_frequencies_12: dict[str,float],
        mw_pulse_ports: dict[str,str],
        mw_pulse_durations: dict[str,float],
        artificial_detuning: float = 0,
        repetitions: int = 1024,
        **intermediate_delays,
        ) -> Schedule:
        sched = Schedule("multiplexed_ramsey_BATCHED",repetitions)

        #Not necessary for f01 Ramsey
        for this_qubit, mw_f_val in mw_frequencies_12.items():
            sched.add_resource(ClockResource( name=mw_clocks_12[this_qubit], freq=mw_f_val))

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = sched.add(Reset(*qubits), label="Reset")

        for acq_cha, (delay_key, delay_array_val) in enumerate(intermediate_delays.items()):
            this_qubit = [qubit for qubit in qubits if qubit in delay_key][0]
            # The second for loop iterates over all frequency values in the frequency batch:
            relaxation = root_relaxation #To enforce parallelism we refer to the root relaxation

            for acq_index, ramsey_delay in enumerate(delay_array_val):
                recovery_phase = np.rad2deg(2 * np.pi * artificial_detuning * ramsey_delay)

                if self.qubit_state == 1:
                    first_excitation = sched.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                    f12_amp = mw_ef_amps180[this_qubit]
                    first_X90 = sched.add(
                        DRAGPulse(
                            duration=mw_pulse_durations[this_qubit],
                            G_amp=f12_amp/2,
                            D_amp=0,
                            port=mw_pulse_ports[this_qubit],
                            clock=mw_clocks_12[this_qubit],
                            phase=0,
                        ),
                        label=f"X90_12_{this_qubit}_{acq_index}", ref_op=first_excitation, ref_pt="end",
                    )

                    second_X90 = sched.add(
                        DRAGPulse(
                            duration=mw_pulse_durations[this_qubit],
                            G_amp=f12_amp/2,
                            D_amp=0,
                            port=mw_pulse_ports[this_qubit],
                            clock=mw_clocks_12[this_qubit],

                            phase=recovery_phase,
                        ),
                        label=f"second_X90_12_{this_qubit}_{acq_index}",rel_time=ramsey_delay, ref_op=first_X90, ref_pt="end",
                    )

                elif self.qubit_state == 0:
                    first_X90 = sched.add(X90(this_qubit), ref_op=relaxation, ref_pt='end')

                    # the phase of the second pi/2 phase progresses to propagate
                    second_X90 = sched.add(
                        Rxy(theta=90, phi=recovery_phase, qubit=this_qubit),
                        ref_op=first_X90,
                        ref_pt="end",
                        rel_time=ramsey_delay
                    )

                if self.qubit_state == 0:
                    measure_function = Measure
                elif self.qubit_state == 1:
                    measure_function = Measure_1

                sched.add(
                    measure_function(this_qubit, acq_index=acq_index, acq_channel=acq_cha, bin_mode=BinMode.AVERAGE),
                    ref_op=second_X90,
                    ref_pt="end",
                    label=f'Measurement_{this_qubit}_{acq_index}',
                )

                # update the relaxation for the next batch point
                relaxation = sched.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{acq_index}")

        return sched
