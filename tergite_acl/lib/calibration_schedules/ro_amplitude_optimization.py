from quantify_scheduler.operations.gate_library import Reset
from quantify_scheduler.operations.pulse_library import SquarePulse, IdlePulse
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.schedules.schedule import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.resources import ClockResource
from tergite_acl.lib.measurement_base import Measurement
from tergite_acl.utils.extended_transmon_element import ExtendedTransmon
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.control_flow_library import Loop
import numpy as np


class RO_amplitude_optimization(Measurement):

    def __init__(self,transmons: dict[str, ExtendedTransmon], qubit_state:int=0):
        super().__init__(transmons)

        self.transmons = transmons
        self.qubit_state = qubit_state
        if self.qubit_state == 1:
            ro_config = 'readout_2state_opt'
        elif self.qubit_state == 2:
            ro_config = 'readout_3state_opt'


    def schedule_function(
        self,
        ro_amplitudes: dict[str,np.ndarray],
        loop_repetitions: int,
        qubit_states: dict[str,np.ndarray]
        ) -> Schedule:

        schedule = Schedule("ro_amplitude_optimization", repetitions=1)

        qubits = self.transmons.keys()

        #Initialize ClockResource with the first frequency value
        # TODO the qubit_state attr needs reworking
        ro_str = 'ro_2st_opt'
        if self.qubit_state == 2:
            ro_str = 'ro_3st_opt'

        for this_qubit, this_transmon in self.transmons.items():
            this_ro_clock = f'{this_qubit}.' + ro_str
            if self.qubit_state == 1:
                ro_frequency = this_transmon.extended_clock_freqs.readout_2state_opt()
            if self.qubit_state == 2:
                ro_frequency = this_transmon.extended_clock_freqs.readout_3state_opt()

            schedule.add_resource(
                ClockResource(name=this_ro_clock, freq=ro_frequency)
            )

        for this_qubit, this_transmon in self.transmons.items():
            mw_frequency_01 = this_transmon.clock_freqs.f01()
            schedule.add_resource(
                ClockResource(name=f'{this_qubit}.01', freq=mw_frequency_01)
            )

        if self.qubit_state == 2:
            for this_qubit, this_transmon in self.transmons.items():
                this_clock = f'{this_qubit}.12'
                mw_frequency_12 = this_transmon.clock_freqs.f12()
                schedule.add_resource(
                    ClockResource(name=this_clock, freq=mw_frequency_12)
                )


        # The outer for-loop iterates over all qubits:
        shot = Schedule(f"shot")
        root_relaxation = shot.add(Reset(*qubits), label="Reset")
        # root_relaxation = shot.add(IdlePulse(20e-9), label="Reset")

        for acq_cha, (this_qubit, ro_amplitude_values) in enumerate(ro_amplitudes.items()):
            # unpack the static parameters:
            this_transmon = self.transmons[this_qubit]
            ro_pulse_duration = this_transmon.measure.pulse_duration()
            mw_amp180 = this_transmon.rxy.amp180()
            mw_ef_amp180 = this_transmon.r12.ef_amp180()
            mw_pulse_duration = this_transmon.rxy.duration()
            mw_pulse_port = this_transmon.ports.microwave()
            mw_motzoi = this_transmon.rxy.motzoi()
            acquisition_delay = this_transmon.measure.acq_delay()
            integration_time = this_transmon.measure.integration_time()
            ro_port = this_transmon.ports.readout()

            this_ro_clock =  f'{this_qubit}.' + ro_str
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

                # The inner for-loop iterates over all qubit levels:
                for level_index, state_level in enumerate(qubit_levels):

                    this_index = ampl_indx * number_of_levels + level_index

                    if state_level == 0:
                        prep = shot.add(IdlePulse(mw_pulse_duration))

                    elif state_level == 1:
                        prep = shot.add(DRAGPulse(
                                    duration=mw_pulse_duration,
                                    G_amp=mw_amp180,
                                    D_amp=mw_motzoi,
                                    port=mw_pulse_port,
                                    clock=this_clock,
                                    phase=0,
                                    ),
                        )
                    elif state_level == 2:
                        shot.add(DRAGPulse(
                                    duration=mw_pulse_duration,
                                    G_amp=mw_amp180,
                                    D_amp=mw_motzoi,
                                    port=mw_pulse_port,
                                    clock=this_clock,
                                    phase=0,
                                    ),
                        )
                        prep = shot.add(
                            DRAGPulse(
                                duration=mw_pulse_duration,
                                G_amp=mw_ef_amp180,
                                D_amp=0,
                                port=mw_pulse_port,
                                clock=this_12_clock,
                                phase=0,
                            ),
                        )
                    else:
                        raise ValueError('State Input Error')

                    ro_pulse = shot.add(
                        SquarePulse(
                            duration=ro_pulse_duration,
                            amp=ro_amplitude,
                            port=ro_port,
                            clock=this_ro_clock,
                        ),

                        ref_op=prep, ref_pt="end",
                        # rel_time=100e-9,
                    )

                    shot.add(
                        SSBIntegrationComplex(
                            duration=integration_time,
                            port=ro_port,
                            clock=this_ro_clock,
                            acq_index=this_index,
                            acq_channel=acq_cha,
                            bin_mode=BinMode.APPEND
                        ),
                        ref_op=ro_pulse, ref_pt="start",
                        rel_time=acquisition_delay,
                    )

                    shot.add(Reset(this_qubit))
                    # shot.add(IdlePulse(20e-9))
        schedule.add(IdlePulse(20e-9))
        # schedule.add(shot, validate=False)
        schedule.add(shot, control_flow=Loop(loop_repetitions), validate=False)
        schedule.add(IdlePulse(20e-9))

        return schedule
