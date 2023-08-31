"""
Module containing a schedule class for resonator spectroscopy calibration.
"""

from quantify_scheduler.enums import BinMode
from quantify_scheduler.schedules.schedule import Schedule
from quantify_scheduler.operations.pulse_library import  SquarePulse, SetClockFrequency, DRAGPulse
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.operations.gate_library import Reset, X
from quantify_scheduler.resources import ClockResource

from calibration_schedules.measurement_base import Measurement
import numpy as np

class RO_frequency_optimization(Measurement):

    def __init__(self,transmons,qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons
        self.static_kwargs = {
            'qubits': self.qubits,
            'pulse_amplitudes': self.attributes_dictionary('pulse_amp'),
            'pulse_durations' : self.attributes_dictionary('pulse_duration'),
            'acquisition_delays': self.attributes_dictionary('acq_delay'),
            'integration_times': self.attributes_dictionary('integration_time'),
            'mw_pulse_durations': self.attributes_dictionary('duration'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
            'mw_frequencies_12': self.attributes_dictionary('f12'),
            'mw_ef_amps180': self.attributes_dictionary('ef_amp180'),
            'ro_ports': self.attributes_dictionary('readout_port'),
        }


    def schedule_function(
        self,
        pulse_amplitudes: dict[str,float],
        pulse_durations: dict[str,float],
        mw_ef_amps180: dict[str,float],
        mw_pulse_durations: dict[str,float],
        mw_pulse_ports: dict[str,str],
        mw_frequencies_12:  dict[str,float],
        acquisition_delays: dict[str,float],
        integration_times: dict[str,float],
        qubits: list[str],
        ro_ports: dict[str,str],
        ro_frequencies: dict[str,np.ndarray],
        repetitions: int = 1024,
        ) -> Schedule:

        sched = Schedule("multiplexed_ro_frequency_optimization",repetitions)

        # Initialize the clock for each qubit

        ro_str = 'ro_opt'

        #Initialize ClockResource with the first frequency value
        for this_qubit, ro_array_val in ro_frequencies.items():
            this_ro_clock = f'{this_qubit}.' + ro_str
            sched.add_resource( ClockResource(name=this_ro_clock, freq=ro_array_val[0]) )

        for this_qubit, ef_f_val in mw_frequencies_12.items():
            this_clock = f'{this_qubit}.12'
            sched.add_resource(ClockResource(name=this_clock, freq=ef_f_val))

        root_relaxation = sched.add(Reset(*qubits), label="Reset")

        # The first for loop iterates over all qubits:
        for acq_cha, (this_qubit, ro_f_values) in enumerate(ro_frequencies.items()):

            sched.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            this_ro_clock = f'{this_qubit}.' + ro_str

            # this_mw_clock = f'{this_qubit}.12'

            # The second for loop iterates over all frequency values in the frequency batch:
            for acq_index, ro_frequency in enumerate(ro_f_values):
                sched.add(
                    SetClockFrequency(clock=this_ro_clock, clock_freq_new=ro_frequency),
                )

                ro_pulse = sched.add(
                    SquarePulse(
                        duration=pulse_durations[this_qubit],
                        amp=pulse_amplitudes[this_qubit],
                        port=ro_ports[this_qubit],
                        clock=this_ro_clock,
                    ),
                )

                sched.add(
                    SSBIntegrationComplex(
                        duration=integration_times[this_qubit],
                        port=ro_ports[this_qubit],
                        clock=this_ro_clock,
                        acq_index=acq_index,
                        acq_channel=acq_cha,
                        bin_mode=BinMode.AVERAGE
                    ),
                    ref_op=ro_pulse, ref_pt="start",
                    rel_time=acquisition_delays[this_qubit],
                )

                sched.add(Reset(this_qubit))

            #shift the acquisition channel
            acq_cha += len(qubits)
            #repeat for when the qubit is at |1>
            for acq_index, ro_frequency in enumerate(ro_f_values):

                sched.add(X(this_qubit))
                sched.add(
                    SetClockFrequency(clock=this_ro_clock, clock_freq_new=ro_frequency),
                )

                ro_pulse = sched.add(
                    SquarePulse(
                        duration=pulse_durations[this_qubit],
                        amp=pulse_amplitudes[this_qubit],
                        port=ro_ports[this_qubit],
                        clock=this_ro_clock,
                    ),
                )

                sched.add(
                    SSBIntegrationComplex(
                        duration=integration_times[this_qubit],
                        port=ro_ports[this_qubit],
                        clock=this_ro_clock,
                        acq_index=acq_index,
                        acq_channel=acq_cha,
                        bin_mode=BinMode.AVERAGE
                    ),
                    ref_op=ro_pulse, ref_pt="start",
                    rel_time=acquisition_delays[this_qubit],
                )

                sched.add(Reset(this_qubit))

        return sched

        #         if self.qubit_state == 0:
        #             pass
        #         elif self.qubit_state == 1:
        #             sched.add(X(this_qubit))
        #         elif self.qubit_state == 2:
        #             sched.add(X(this_qubit))
        #             sched.add(
        #                 DRAGPulse(
        #                     duration=mw_pulse_durations[this_qubit],
        #                     G_amp=mw_ef_amps180[this_qubit],
        #                     D_amp=0,
        #                     port=mw_pulse_ports[this_qubit],
        #                     clock=this_mw_clock,
        #                     phase=0,
        #                 ),
        #             )
        #
        #         ro_pulse = sched.add(
        #             SquarePulse(
        #                 duration=pulse_durations[this_qubit],
        #                 amp=pulse_amplitudes[this_qubit],
        #                 port=ro_ports[this_qubit],
        #                 clock=this_ro_clock,
        #             ),
        #         )
        #
        #         sched.add(
        #             SSBIntegrationComplex(
        #                 duration=integration_times[this_qubit],
        #                 port=ro_ports[this_qubit],
        #                 clock=this_ro_clock,
        #                 acq_index=acq_index,
        #                 acq_channel=acq_cha,
        #                 bin_mode=BinMode.AVERAGE
        #             ),
        #             ref_op=ro_pulse, ref_pt="start",
        #             rel_time=acquisition_delays[this_qubit],
        #         )
        #
        #         sched.add(Reset(this_qubit))
        #
        # return sched
