"""
Module containing a schedule class for resonator spectroscopy calibration.
"""

from quantify_scheduler.enums import BinMode
from quantify_scheduler.schedules.schedule import Schedule
from quantify_scheduler.operations.pulse_library import  SquarePulse, SetClockFrequency, DRAGPulse
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.operations.gate_library import Reset, X
from quantify_scheduler.resources import ClockResource

from tergite_acl.lib.measurement_base import Measurement
from tergite_acl.utils.extended_transmon_element import ExtendedTransmon
import numpy as np

class RO_frequency_optimization(Measurement):

    def __init__(self,transmons: dict[str, ExtendedTransmon], qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons


    def schedule_function(
        self,
        ro_opt_frequencies: dict[str,np.ndarray],
        repetitions: int = 1024,
        ) -> Schedule:

        sched = Schedule("multiplexed_ro_frequency_optimization", repetitions)

        qubits = self.transmons.keys()

        # Initialize the clock for each qubit

        # TODO the qubit_state attr needs reworking
        ro_str = 'ro_2st_opt'
        if self.qubit_state == 2:
            ro_str = 'ro_3st_opt'

        #Initialize ClockResource with the first frequency value
        for this_qubit, ro_array_val in ro_opt_frequencies.items():
            this_ro_clock = f'{this_qubit}.' + ro_str
            sched.add_resource(ClockResource(name=this_ro_clock, freq=ro_array_val[0]))

        for this_qubit, this_transmon in self.transmons.items():
            mw_frequency_12 = this_transmon.clock_freqs.f12()
            this_clock = f'{this_qubit}.12'
            schedule.add_resource(ClockResource(name=this_clock, freq=mw_frequency_12))

        root_relaxation = sched.add(Reset(*qubits), label="Reset")

        # The first for loop iterates over all qubits:
        for acq_cha, (this_qubit, ro_f_values) in enumerate(ro_opt_frequencies.items()):

            # unpack the static parameters
            this_transmon = self.transmons[this_qubit]
            ro_pulse_amplitude = this_transmon.measure.pulse_amp()
            ro_pulse_duration = this_transmon.measure.pulse_duration()
            mw_pulse_duration = this_transmon.rxy.duration()
            mw_pulse_port = this_transmon.ports.microwave()
            acquisition_delay = this_transmon.measure.acq_delay()
            integration_time = this_transmon.measure.integration_time()
            ro_port = this_transmon.ports.readout()

            sched.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            this_ro_clock = f'{this_qubit}.' + ro_str

            this_mw_clock = f'{this_qubit}.12'

            # The second for loop iterates over all frequency values in the frequency batch:
            for acq_index, ro_frequency in enumerate(ro_f_values):
                sched.add(
                    SetClockFrequency(clock=this_ro_clock, clock_freq_new=ro_frequency),
                )
                ro_pulse = sched.add(
                    SquarePulse(
                        duration=ro_pulse_duration,
                        amp=ro_pulse_amplitude,
                        port=ro_port,
                        clock=this_ro_clock,
                    ),
                )

                sched.add(
                    SSBIntegrationComplex(
                        duration=integration_time,
                        port=ro_port,
                        clock=this_ro_clock,
                        acq_index=acq_index,
                        acq_channel=acq_cha,
                        bin_mode=BinMode.AVERAGE
                    ),
                    ref_op=ro_pulse, ref_pt="start",
                    rel_time=acquisition_delay,
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
                        duration=ro_pulse_duration,
                        amp=ro_pulse_amplitude,
                        port=ro_port,
                        clock=this_ro_clock,
                    ),
                )

                sched.add(
                    SSBIntegrationComplex(
                        duration=integration_time,
                        port=ro_port,
                        clock=this_ro_clock,
                        acq_index=acq_index,
                        acq_channel=acq_cha,
                        bin_mode=BinMode.AVERAGE
                    ),
                    ref_op=ro_pulse, ref_pt="start",
                    rel_time=acquisition_delay,
                )

                sched.add(Reset(this_qubit))

            if self.qubit_state == 2:
                #shift the acquisition channel
                acq_cha += len(qubits)
                #repeat for when the qubit is at |2>
                for acq_index, ro_frequency in enumerate(ro_f_values):
                    sched.add(X(this_qubit))
                    sched.add(
                        DRAGPulse(
                            duration=mw_pulse_duration,
                            G_amp=mw_ef_amps180,
                            D_amp=0,
                            port=mw_pulse_port,
                            clock=this_mw_clock,
                            phase=0,
                        ),
                    )

                    sched.add(
                        SetClockFrequency(clock=this_ro_clock, clock_freq_new=ro_frequency),
                    )

                    ro_pulse = sched.add(
                        SquarePulse(
                            duration=ro_pulse_duration,
                            amp=ro_pulse_amplitude,
                            port=ro_port,
                            clock=this_ro_clock,
                        ),
                    )

                    sched.add(
                        SSBIntegrationComplex(
                            duration=integration_time,
                            port=ro_port,
                            clock=this_ro_clock,
                            acq_index=acq_index,
                            acq_channel=acq_cha,
                            bin_mode=BinMode.AVERAGE
                        ),
                        ref_op=ro_pulse, ref_pt="start",
                        rel_time=acquisition_delay,
                    )

                    sched.add(Reset(this_qubit))

        return sched
