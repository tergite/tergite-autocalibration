from quantify_scheduler.resources import ClockResource
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from calibration_schedules.measurement_base import Measurement

# from transmon_element import Measure_1

class Rabi_Oscillations(Measurement):

    def __init__(self,transmons,connections,qubit_state:int=0):
        super().__init__(transmons,connections)
        self.experiment_parameters = 'mw_amp180_BATCHED'
        self.gettable_batched = True
        self.qubit_state = qubit_state
        self.static_kwargs = {
            'qubits': self.qubits,
            'mw_frequencies': self._get_attributes('freq_01'),
            'mw_frequencies_12': self._get_attributes('freq_12'),
            'mw_clocks': self._get_attributes('mw_01_clock'),
            'mw_clocks_12': self._get_attributes('mw_12_clock'),
            'mw_pulse_ports': self._get_attributes('mw_port'),
            'mw_pulse_durations': self._get_attributes('mw_pulse_duration'),
        }

    def settables_dictionary(self):
        parameters = self.experiment_parameters
        manual_parameter = 'mw_amp180_BATCHED'
        assert( manual_parameter in self.experiment_parameters )
        mp_data = {
            manual_parameter : {
                'name': manual_parameter,
                'initial_value': 1e-4,
                'unit': 'V',
                'batched': True
            }
        }
        return self._settables_dictionary(parameters, isBatched=self.gettable_batched, mp_data=mp_data)

    def setpoints_array(self):
        return self._setpoints_1d_array()

    def schedule_function(
        self,
        qubits: list[str],
        mw_frequencies: dict[str,float],
        mw_frequencies_12: dict[str,float],
        mw_pulse_ports: dict[str,str],
        mw_clocks: dict[str,str],
        mw_clocks_12: dict[str,str],
        mw_pulse_durations: dict[str,float],
        repetitions: int = 1024,
        **mw_amplitudes,
        ) -> Schedule:

        if self.qubit_state == 0:
            schedule_title = "multiplexed_rabi_01_BATCHED"
            measure_function = Measure
        elif self.qubit_state == 1:
            schedule_title = "multiplexed_rabi_12_BATCHED"
            measure_function = Measure_1
        else:
            raise ValueError(f'Invalid qubit state: {self.qubit_state}')

        sched = Schedule(schedule_title,repetitions)

        for this_qubit, mw_f_val in mw_frequencies.items():
            sched.add_resource(
                ClockResource( name=f'{this_qubit}.01', freq=mw_f_val)
            )
        for this_qubit, mw_f_val in mw_frequencies_12.items():
            sched.add_resource(
                ClockResource( name=f'{this_qubit}.12', freq=mw_f_val)
            )

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = sched.add(Reset(*qubits), label="Reset")

        for acq_cha, (mw_amp_key, mw_amp_array_val) in enumerate(mw_amplitudes.items()):
            this_qubit = [qubit for qubit in qubits if qubit in mw_amp_key][0]
            if self.qubit_state == 0:
                this_clock = mw_clocks[this_qubit]
            elif self.qubit_state == 1:
                this_clock = mw_clocks_12[this_qubit]
            else:
                raise ValueError(f'Invalid qubit state: {self.qubit_state}')
            # The second for loop iterates over all frequency values in the frequency batch:
            relaxation = root_relaxation #To enforce parallelism we refer to the root relaxation
            for acq_index, mw_amplitude in enumerate(mw_amp_array_val):
                if self.qubit_state == 1:
                    relaxation = sched.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                mw_pulse = sched.add(
                    DRAGPulse(
                        duration=mw_pulse_durations[this_qubit],
                        G_amp=mw_amplitude,
                        D_amp=0,
                        port=mw_pulse_ports[this_qubit],
                        clock=this_clock,
                        phase=0,
                    ),
                    label=f"rabi_pulse_{this_qubit}_{acq_index}", ref_op=relaxation, ref_pt="end",
                )


                sched.add(
                    measure_function(this_qubit, acq_index=acq_index, acq_channel=acq_cha, bin_mode=BinMode.AVERAGE),
                    label=f'Measurement_{this_qubit}_{acq_index}',
                    ref_op=mw_pulse,
                    ref_pt="end",
                )

                # update the relaxation for the next batch point
                relaxation = sched.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{acq_index}")

        return sched
