from quantify_scheduler.operations.gate_library import Reset, X, Rxy
from quantify_scheduler.operations.pulse_library import SquarePulse, SetClockFrequency, IdlePulse
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.schedules.schedule import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.resources import ClockResource
from calibration_schedules.measurement_base import Measurement
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.control_flow_library import Loop
import numpy as np

class RO_amplitude_optimization(Measurement):

    def __init__(self,transmons,qubit_state:int=0):
        super().__init__(transmons)

        self.transmons = transmons
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
            'pulse_durations': self.attributes_dictionary('pulse_duration'),
            'acquisition_delays': self.attributes_dictionary('acq_delay'),
            'integration_times': self.attributes_dictionary('integration_time'),
            'ro_ports': self.attributes_dictionary('readout_port'),
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
        ro_amplitudes: dict[str,np.ndarray],
        loop_repetitions: int,
        qubit_states: dict[str,np.ndarray]

        ) -> Schedule:

        schedule = Schedule("ro_amplitude_optimization", repetitions=1)

        print(f'{ loop_repetitions = }')

        #Initialize ClockResource with the first frequency value
        ro_str = 'ro_opt'

        for this_qubit, ro_array_val in ro_opt_frequency.items():
            this_ro_clock = f'{this_qubit}.' + ro_str
            schedule.add_resource(
                ClockResource(name=this_ro_clock, freq=ro_array_val)
            )

        for this_qubit, mw_f_val in mw_frequencies.items():
            schedule.add_resource(
                ClockResource(name=f'{this_qubit}.01', freq=mw_f_val)
            )

        for this_qubit, ef_f_val in mw_frequencies_12.items():
            this_clock = f'{this_qubit}.12'
            schedule.add_resource(
                ClockResource(name=this_clock, freq=ef_f_val)
            )


        # The outer for-loop iterates over all qubits:
        shot = Schedule(f"shot")
        root_relaxation = shot.add(Reset(*qubits), label="Reset")
        # root_relaxation = shot.add(IdlePulse(20e-9), label="Reset")

        for acq_cha, (this_qubit, ro_amplitude_values) in enumerate(ro_amplitudes.items()):

            this_ro_clock = this_qubit + '.ro_opt'
            this_clock = f'{this_qubit}.01'
            this_12_clock = f'{this_qubit}.12'

            # qubit_levels = range(self.qubit_state + 1)
            # this is to simplify the configuration of the raw dataset
            qubit_levels = np.unique(qubit_states[this_qubit])

            number_of_levels = len(qubit_levels)

            # To enforce parallelism we refer to the root relaxation
            shot.add(Reset(*qubits), ref_op=root_relaxation, ref_pt_new='end')

            # The intermediate for-loop iterates over all ro_amplitudes:
            for ampl_indx, ro_amplitude in enumerate(ro_amplitude_values):
                print(f'{ ro_amplitude = }')

                # The inner for-loop iterates over all qubit levels:
                for level_index, state_level in enumerate(qubit_levels):

                    this_index = ampl_indx * number_of_levels + level_index
                    print(f'{ this_index = }')

                    if state_level == 0:
                        prep = shot.add(IdlePulse(mw_pulse_durations[this_qubit]))

                    elif state_level == 1:
                        prep = shot.add(DRAGPulse(
                                    duration=mw_pulse_durations[this_qubit],
                                    G_amp=mw_amplitudes[this_qubit],
                                    D_amp=mw_motzois[this_qubit],
                                    port=mw_pulse_ports[this_qubit],
                                    clock=this_clock,
                                    phase=0,
                                    ),
                        )
                    elif state_level == 2:
                        shot.add(DRAGPulse(
                                    duration=mw_pulse_durations[this_qubit],
                                    G_amp=mw_amplitudes[this_qubit],
                                    D_amp=mw_motzois[this_qubit],
                                    port=mw_pulse_ports[this_qubit],
                                    clock=this_clock,
                                    phase=0,
                                    ),
                        )
                        prep = shot.add(
                            DRAGPulse(
                                duration=mw_pulse_durations[this_qubit],
                                G_amp=mw_ef_amp180[this_qubit],
                                D_amp=0,
                                port=mw_pulse_ports[this_qubit],
                                clock=this_12_clock,
                                phase=0,
                            ),
                        )
                    else:
                        raise ValueError('State Input Error')

                    ro_pulse = shot.add(
                        SquarePulse(
                            duration=pulse_durations[this_qubit],
                            amp=ro_amplitude,
                            port=ro_ports[this_qubit],
                            clock=this_ro_clock,
                        ),

                        ref_op=prep, ref_pt="end",
                        # rel_time=100e-9,
                    )

                    shot.add(
                        SSBIntegrationComplex(
                            duration=integration_times[this_qubit],
                            port=ro_ports[this_qubit],
                            clock=this_ro_clock,
                            acq_index=this_index,
                            acq_channel=acq_cha,
                            bin_mode=BinMode.APPEND
                        ),
                        ref_op=ro_pulse, ref_pt="start",
                        rel_time=acquisition_delays[this_qubit],
                    )

                    shot.add(Reset(this_qubit))
                    # shot.add(IdlePulse(20e-9))
        schedule.add(IdlePulse(20e-9))
        # schedule.add(shot, validate=False)
        schedule.add(shot, control_flow=Loop(loop_repetitions), validate=False)
        schedule.add(IdlePulse(20e-9))

        return schedule
