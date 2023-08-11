"""
Module containing a schedule class for Ramsey calibration.
"""
from quantify_scheduler.resources import ClockResource
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X
from measurements_base import Measurement_base
from transmon_element import Measure_1
import numpy as np

class Ramsey_Detunings(Measurement_base):

    def __init__(self,transmons,connections,qubit_state:int=0):
        super().__init__(transmons,connections)
        self.experiment_parameters = ['ramsey_delay_BATCHED', 'artificial_detuning'] # The order matters
        self.parameter_order = ['ramsey_delay_BATCHED', 'artificial_detuning'] # The order matters
        self.gettable_batched = True
        self.qubit_state = qubit_state
        self.static_kwargs = {
            'qubits': self.qubits,
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

        manual_parameter = 'artificial_detuning'
        assert( manual_parameter in self.experiment_parameters )
        mp_data.update( {
            manual_parameter: {
                'name': manual_parameter,
                'initial_value': 0,
                'unit': 'Hz',
                'batched': False
            }
        })
        return self._settables_dictionary(parameters, isBatched=self.gettable_batched, mp_data=mp_data)

    def setpoints_array(self):
        return self._setpoints_Nd_array()

    def schedule_function(
        self,
        qubits: list[str],

        mw_clocks_12: dict[str,str],
        mw_ef_amps180: dict[str,float],
        mw_frequencies_12: dict[str,float],
        mw_pulse_ports: dict[str,str],
        mw_pulse_durations: dict[str,float],
        repetitions: int = 1024,
        **ramsey_detunings_and_delays,
        ) -> Schedule:
        """
        Generate a schedule for performing a Ramsey fringe measurement on multiple qubits. 
        Can be used both to finetune the qubit frequency and to measure the qubit dephasing time T_2.

        Schedule sequence
            Reset -> pi/2 pulse -> Idle(tau) -> pi/2 pulse -> Measure
        
        Parameters
        ----------
        self
            Contains all qubit states.
        qubits
            The list of qubits on which to perform the experiment.
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
        repetitions
            The amount of times the Schedule will be repeated.
        **ramsey_detunings_and_delays
            2D sweeping parameter arrays.
            Delays: The wait times tau between the pi/2 pulses
            Detunings: The artificial detunings of the qubit frequencies, which is implemented by changing 
            the phase of the second pi/2 pulse. 
            

        Returns
        -------
        :
            An experiment schedule.
        """

        PI = 3.14159265359

        schedule = Schedule("mltplx_ramsey_detunings",repetitions)

        #Not necessary for f01 Ramsey
        for this_qubit, mw_f_val in mw_frequencies_12.items():
            schedule.add_resource(ClockResource( name=mw_clocks_12[this_qubit], freq=mw_f_val))

        ramsey_parameters = {qubit:{} for qubit in qubits}
        for ramsey_key, ramsey_val in ramsey_detunings_and_delays.items():
            this_qubit = [q for q in qubits if q in ramsey_key][0]
            if 'delay' in ramsey_key:
               ramsey_parameters[this_qubit].update({'ramsey_delay':ramsey_val})
            if 'artificial' in ramsey_key:
               ramsey_parameters[this_qubit].update({'artificial_detuning':ramsey_val})

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        for acq_cha, (values_key, values_val) in enumerate(ramsey_parameters.items()):
            this_qubit = [q for q in qubits if q in values_key][0]

            # ramsey_delays is an array
            ramsey_delays = values_val['ramsey_delay']
            artificial_detuning = values_val['artificial_detuning']

            relaxation = schedule.add(
                Reset(*qubits), label=f'Reset_{acq_cha}', ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            # The second for loop iterates over all ramsey delays values in the ramsey_delay batch:
            for acq_index, ramsey_delay in enumerate(ramsey_delays):

                recovery_phase = np.rad2deg(2 * PI * artificial_detuning * ramsey_delay)

                if self.qubit_state == 1:
                    first_excitation = schedule.add(X(this_qubit))
                    f12_amp = mw_ef_amps180[this_qubit]
                    first_X90 = schedule.add(
                        DRAGPulse(
                            duration=mw_pulse_durations[this_qubit],
                            G_amp=f12_amp/2,
                            D_amp=0,
                            port=mw_pulse_ports[this_qubit],
                            clock=mw_clocks_12[this_qubit],
                            phase=0,
                        ),
                        label=f"X90_12_{this_qubit}_{acq_index}"
                    )

                    second_X90 = schedule.add(
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
                    first_X90 = schedule.add(X90(this_qubit))

                    # the phase of the second pi/2 phase progresses to propagate
                    second_X90 = schedule.add(
                        Rxy(theta=90, phi=recovery_phase, qubit=this_qubit),
                        ref_op=first_X90,
                        ref_pt="end",
                        rel_time=ramsey_delay
                    )
                else:
                    raise ValueError(f'Invalid qubit state: {self.qubit_state}')

                if self.qubit_state == 0:
                    measure_function = Measure
                elif self.qubit_state == 1:
                    measure_function = Measure_1
                else:
                    raise ValueError(f'Invalid qubit state: {self.qubit_state}')

                schedule.add(
                    measure_function(this_qubit, acq_index=acq_index, acq_channel=acq_cha, bin_mode=BinMode.AVERAGE),
                    ref_op=second_X90,
                    ref_pt="end",
                    label=f'Measurement_{this_qubit}_{acq_index}',
                )

                # update the relaxation for the next batch point
                schedule.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{acq_index}")
        return schedule
