import numpy as np
from quantify_scheduler.backends.qblox.operations.gate_library import ConditionalReset
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.gate_library import Measure, Reset, X
from quantify_scheduler.operations.pulse_factories import long_square_pulse
from quantify_scheduler.operations.pulse_library import (
    IdlePulse,
    SetClockFrequency,
    SoftSquarePulse,
)
from quantify_scheduler.resources import ClockResource
from quantify_scheduler.schedules.schedule import Schedule

from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.extended_gates import Measure_RO1
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon


class Two_Tones_Multidim_AR(BaseMeasurement):
    def __init__(self, transmons: dict[str, ExtendedTransmon], qubit_state: int = 0):
        super().__init__(transmons)

        self.qubit_state = qubit_state
        self.transmons = transmons

    def schedule_function(
        self,
        spec_frequencies: dict[str, np.ndarray],
        spec_pulse_amplitudes: dict[str, np.ndarray] = None,
    ) -> Schedule:

        schedule = Schedule("multiplexed_qubit_spec_AR", repetitions=1024)

        # Initialize the clock for each qubit
        # Initialize ClockResource with the first frequency value
        for this_qubit, spec_array_val in spec_frequencies.items():
            if self.qubit_state == 0:
                schedule.add_resource(
                    ClockResource(name=f"{this_qubit}.01", freq=spec_array_val[0])
                )
            elif self.qubit_state == 1:
                schedule.add_resource(
                    ClockResource(name=f"{this_qubit}.12", freq=spec_array_val[0])
                )
            else:
                raise ValueError(f"Invalid qubit state: {self.qubit_state}")

        qubits = self.transmons.keys()

        if self.qubit_state == 0:
            measure_function = Measure
        elif self.qubit_state == 1:
            measure_function = Measure_RO1
        else:
            raise ValueError(f"Invalid qubit state: {self.qubit_state}")

        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer loop, iterates over all qubits
        for acq_channel, (this_qubit, spec_pulse_frequency_values) in enumerate(
            spec_frequencies.items()
        ):
            # unpack the static parameters
            this_transmon = self.transmons[this_qubit]
            spec_pulse_duration = this_transmon.spec.spec_duration()
            mw_pulse_port = this_transmon.ports.microwave()
            ro_duration = this_transmon.measure.pulse_duration()
            rxy_duration = this_transmon.rxy.duration()

            print(f"{ ro_duration = }")
            print(f"{ rxy_duration = }")
            cr_duration = 364e-9 + ro_duration + rxy_duration + 4e-9
            ar_stagger_time = acq_channel * cr_duration
            ar_buffer_time = len(qubits) * cr_duration
            # TODO: this can be refined:
            spectroscopy_time = ro_duration + spec_pulse_duration
            measurement_stagger_time = acq_channel * (ro_duration + 252e-9)
            measurement_buffer_time = len(qubits) * (spectroscopy_time + 252e-9)

            # long pulses require more efficient memory management
            if spec_pulse_duration > 6.5e-6:
                SpectroscopyPulse = long_square_pulse
            else:
                SpectroscopyPulse = SoftSquarePulse

            if spec_pulse_amplitudes is None:
                spec_amplitude = this_transmon.spec.spec_ampl_optimal()
                print(
                    f"setting optimal spec_amplitude for {this_qubit} {spec_amplitude}"
                )
                amplitude_values = [spec_amplitude]
            else:
                amplitude_values = spec_pulse_amplitudes[this_qubit]

            if self.qubit_state == 0:
                this_clock = f"{this_qubit}.01"
            elif self.qubit_state == 1:
                this_clock = f"{this_qubit}.12"
            else:
                raise ValueError(f"Invalid qubit state: {self.qubit_state}")

            number_of_ampls = len(amplitude_values)

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt="end"
            )  # To enforce parallelism we refer to the root relaxation

            # The intermediate loop iterates over all frequency values
            for freq_indx, spec_pulse_frequency in enumerate(
                spec_pulse_frequency_values
            ):
                # reset the clock frequency for the qubit pulse
                schedule.add(
                    SetClockFrequency(
                        clock=this_clock, clock_freq_new=spec_pulse_frequency
                    ),
                )

                # The inner loop, iterates over all spec_amplitudes
                for acq_index, spec_pulse_amplitude in enumerate(amplitude_values):

                    this_index = freq_indx * number_of_ampls + acq_index

                    if self.qubit_state == 0:
                        pass
                    elif self.qubit_state == 1:
                        schedule.add(X(this_qubit))
                    else:
                        raise ValueError(f"Invalid qubit state: {self.qubit_state}")

                    # ACTIVE RESET BLOCK, the buffer and stagger times ensure that
                    # the conditional operations do not overlap  #################
                    schedule.add(IdlePulse(ar_stagger_time))
                    schedule.add(ConditionalReset(this_qubit, acq_index=2 * this_index))
                    schedule.add(
                        IdlePulse(ar_buffer_time - ar_stagger_time - cr_duration)
                    )
                    ##############################################################

                    # Stagger also the Spectroscopy measurements to avoid trigger overlapings
                    schedule.add(IdlePulse(measurement_stagger_time))
                    schedule.add(
                        SpectroscopyPulse(
                            duration=spec_pulse_duration,
                            amp=spec_pulse_amplitude,
                            port=mw_pulse_port,
                            clock=this_clock,
                        ),
                    )

                    schedule.add(
                        measure_function(
                            this_qubit,
                            # acq_index=this_index,
                            acq_index=2 * this_index + 1,
                            bin_mode=BinMode.AVERAGE,
                            acq_protocol="ThresholdedAcquisition",
                        ),
                    )
                    schedule.add(
                        IdlePulse(
                            measurement_buffer_time
                            - measurement_stagger_time
                            - spectroscopy_time
                        )
                    )

        return schedule
