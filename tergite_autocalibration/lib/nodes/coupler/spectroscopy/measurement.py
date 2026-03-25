# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2026
# (C) Copyright Chalmers Next Labs 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


import numpy as np
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.operations.gate_library import Measure, Reset
from quantify_scheduler.operations.pulse_factories import long_square_pulse
from quantify_scheduler.operations.pulse_library import (
    SetClockFrequency,
    SoftSquarePulse,
    SquarePulse,
)
from quantify_scheduler.resources import ClockResource
from quantify_scheduler.schedules.schedule import Schedule

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon
from tergite_autocalibration.utils.logging import logger


class CouplerSpectroscopyMeasurement(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], *args):
        super().__init__(transmons)

        self.transmons = transmons

    def schedule_function(
        self,
        qubit_frequencies: dict[str, np.ndarray],
        resonator_frequencies: dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:

        schedule = Schedule("coupler_spectroscopy", repetitions)

        qubits = self.transmons.keys()

        # Initialize ClockResource with the first frequency value
        for this_qubit in qubits:
            qubit_spec_frequencies = qubit_frequencies[this_qubit]
            ro_spec_frequencies = resonator_frequencies[this_qubit]
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.01", freq=qubit_spec_frequencies[0])
            )
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.ro", freq=ro_spec_frequencies[0])
            )

        # This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer loop, iterates over all qubits
        for this_qubit, qubit_spec_frequencies in qubit_frequencies.items():
            # unpack the static parameters
            this_transmon = self.transmons[this_qubit]
            spec_pulse_duration = this_transmon.spec.spec_duration()
            mw_pulse_port = this_transmon.ports.microwave()

            spec_pulse_amplitude = this_transmon.spec.spec_ampl_optimal()

            # assign qubit spectroscopy pulse based on duration so long pulses can fit in memory
            if spec_pulse_duration > 6e-6:
                SpectroscopyPulse = long_square_pulse
            else:
                SpectroscopyPulse = SoftSquarePulse

            this_clock = f"{this_qubit}.01"

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation
            )  # To enforce parallelism we refer to the root relaxation

            # The intermediate loop iterates over all frequency values in the frequency batch:
            for this_index, qubit_frequency in enumerate(qubit_spec_frequencies):
                # reset the clock frequency for the qubit pulse
                schedule.add(
                    SetClockFrequency(clock=this_clock, clock_freq_new=qubit_frequency),
                )

                schedule.add(
                    SpectroscopyPulse(
                        duration=spec_pulse_duration,
                        amp=spec_pulse_amplitude,
                        port=mw_pulse_port,
                        clock=this_clock,
                    ),
                )

                schedule.add(
                    Measure(this_qubit, acq_index=this_index),
                )

                # update the relaxation for the next batch point
                schedule.add(Reset(this_qubit))

        for this_qubit, ro_spec_frequencies in resonator_frequencies.items():
            qubit_spec_frequencies = qubit_frequencies[this_qubit]
            number_of_frequencies = len(qubit_spec_frequencies)

            # unpack the static parameters
            this_transmon = self.transmons[this_qubit]
            ro_pulse_amplitude = this_transmon.measure.pulse_amp()
            ro_pulse_duration = this_transmon.measure.pulse_duration()
            acq_channel = this_transmon.measure.acq_channel()
            mw_pulse_port = this_transmon.ports.microwave()
            acquisition_delay = this_transmon.measure.acq_delay()
            integration_time = this_transmon.measure.integration_time()
            ro_port = this_transmon.ports.readout()
            this_ro_clock = f"{this_qubit}.ro"

            for ro_index, ro_frequency in enumerate(ro_spec_frequencies):
                acq_index = number_of_frequencies + ro_index
                schedule.add(
                    SetClockFrequency(clock=this_ro_clock, clock_freq_new=ro_frequency),
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
                        acq_channel=acq_channel,
                        bin_mode=BinMode.AVERAGE,
                    ),
                    ref_op=ro_pulse,
                    ref_pt="start",
                    rel_time=acquisition_delay,
                )

                schedule.add(Reset(this_qubit))
        return schedule
