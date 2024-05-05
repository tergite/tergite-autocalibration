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

class Resonator_Spectroscopy(Measurement):

    def __init__(self,transmons: dict[str, ExtendedTransmon], qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons

    def schedule_function(
        self,
        ro_frequencies: dict[str,np.ndarray],
        repetitions: int = 1024,
        ) -> Schedule:
        """
        Generate a schedule for performing resonator spectroscopy to locate the resonators resonance frequency for multiple qubits.

        Schedule sequence
            Reset -> Spectroscopy pulse -> SSBIntegrationComplex (Measurement)

        Parameters
        ----------
        ro_frequencies
            The sweeping frequencies of the spectroscopy pulse for each qubit.
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """

        schedule = Schedule("multiplexed_resonator_spectroscopy",repetitions)

        qubits = self.transmons.keys()

        # Initialize the clock for each qubit
        if self.qubit_state == 0: ro_str = 'ro'
        elif self.qubit_state == 1: ro_str = 'ro1'
        elif self.qubit_state == 2: ro_str = 'ro2'
        else:
            raise ValueError('error state')

        #Initialize ClockResource with the first frequency value
        for this_qubit, ro_array_val in ro_frequencies.items():
            this_ro_clock = f'{this_qubit}.' + ro_str
            schedule.add_resource( ClockResource(name=this_ro_clock, freq=ro_array_val[0]) )

        if self.qubit_state == 2:
            for this_qubit, this_transmon in self.transmons.items():
                this_clock = f'{this_qubit}.12'
                mw_frequency_12 = this_transmon.clock_freqs.f12()
                schedule.add_resource(ClockResource(name=this_clock, freq=mw_frequency_12))

        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer for loop iterates over all qubits:
        for acq_cha, (this_qubit, ro_f_values) in enumerate(ro_frequencies.items()):

            # unpack the static parameters
            this_transmon = self.transmons[this_qubit]
            ro_pulse_amplitude = this_transmon.measure.pulse_amp()
            ro_pulse_duration = this_transmon.measure.pulse_duration()
            mw_ef_amp180 = this_transmon.r12.ef_amp180()
            mw_pulse_duration = this_transmon.rxy.duration()
            mw_pulse_port = this_transmon.ports.microwave()
            acquisition_delay = this_transmon.measure.acq_delay()
            integration_time = this_transmon.measure.integration_time()
            ro_port = this_transmon.ports.readout()

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt='end'
            ) #To enforce parallelism we refer to the root relaxation

            this_ro_clock = f'{this_qubit}.' + ro_str
            this_mw_clock = f'{this_qubit}.12'

            # The second for loop iterates over all frequency values in the frequency batch:
            for acq_index, ro_frequency in enumerate(ro_f_values):
                schedule.add(
                    SetClockFrequency(clock=this_ro_clock, clock_freq_new=ro_frequency),
                )

                if self.qubit_state == 0:
                    pass
                elif self.qubit_state == 1:
                    schedule.add(X(this_qubit))
                elif self.qubit_state == 2:
                    schedule.add(X(this_qubit))
                    schedule.add(
                        DRAGPulse(
                            duration=mw_pulse_duration,
                            G_amp=mw_ef_amp180,
                            D_amp=0,
                            port=mw_pulse_port,
                            clock=this_mw_clock,
                            phase=0,
                        ),
                    )

                ro_pulse = schedule.add(
                    SquarePulse(
                        duration=ro_pulse_duration,
                        amp=ro_pulse_amplitude,
                        port=ro_port,
                        clock=this_ro_clock,
                    ),
                )

                schedule.add(
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

                schedule.add(Reset(this_qubit))

        return schedule
