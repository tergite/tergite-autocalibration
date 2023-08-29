from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.resources import ClockResource
from calibration_schedules.measurement_base import Measurement
from utilities.extended_transmon_element import Measure_RO1

import numpy as np

class Ramsey_fringes(Measurement):

    def __init__(self,transmons,qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state

        self.static_kwargs = {
            'qubits': self.qubits,
            'artificial_detunings': self.attributes_dictionary('artificial_detuning'),
            'mw_pulse_durations': self.attributes_dictionary('duration'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
            'mw_ef_amps180': self.attributes_dictionary('ef_amp180'),
            'mw_frequencies_12': self.attributes_dictionary('f12'),
        }


    def schedule_function(
            self,
            qubits: list[str],
            artificial_detunings: dict[str,float],
            mw_ef_amps180: dict[str,float],
            mw_frequencies_12: dict[str,float],
            mw_pulse_ports: dict[str,str],
            mw_pulse_durations: dict[str,float],
            ramsey_delays: dict[str,np.ndarray],
            repetitions: int = 1024,
        ) -> Schedule:

        if self.qubit_state == 0:
            schedule_title = "multiplexed_ramsey_01"
            measure_function = Measure
        elif self.qubit_state == 1:
            schedule_title = "multiplexed_ramsey_12"
            measure_function = Measure_RO1
        else:
            raise ValueError(f'Invalid qubit state: {self.qubit_state}')

        sched = Schedule(schedule_title,repetitions)

        for this_qubit, mw_f_val in mw_frequencies_12.items():
            sched.add_resource(
                ClockResource(name=f'{this_qubit}.12', freq=mw_f_val)
            )

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = sched.add(Reset(*qubits), label="Reset")

        for this_qubit, delay_array_val in ramsey_delays.items():
            # The second for loop iterates over all frequency values in the frequency batch:
            relaxation = root_relaxation # To enforce parallelism we refer to the root relaxation
            artificial_detuning = artificial_detunings[this_qubit]

            if self.qubit_state == 1:
                this_clock = f'{this_qubit}.12'
                measure_function = Measure_RO1
            elif self.qubit_state == 0:
                measure_function = Measure
                this_clock = f'{this_qubit}.01'
            else:
                raise ValueError(f'Invalid qubit state: {self.qubit_state}')

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
                            clock=this_clock,
                            phase=0,
                        ),
                        ref_op=first_excitation, ref_pt="end",
                    )

                    second_X90 = sched.add(
                        DRAGPulse(
                            duration=mw_pulse_durations[this_qubit],
                            G_amp=f12_amp/2,
                            D_amp=0,
                            port=mw_pulse_ports[this_qubit],
                            clock=this_clock,

                            phase=recovery_phase,
                        ),
                        rel_time=ramsey_delay, ref_op=first_X90, ref_pt="end",
                    )

                if self.qubit_state == 0:

                    first_X90 = sched.add(X90(this_qubit), ref_op=relaxation, ref_pt='end')

                    # the phase of the second pi/2 phase progresses to propagate
                    second_X90 = sched.add(
                        Rxy(theta=90, phi=recovery_phase, qubit=this_qubit),
                        ref_op=first_X90,
                        ref_pt="end",
                        rel_time=ramsey_delay
                    )

                sched.add(
                    measure_function(this_qubit, acq_index=acq_index, bin_mode=BinMode.AVERAGE),
                    ref_op=second_X90,
                    ref_pt="end",
                )

                # update the relaxation for the next batch point
                relaxation = sched.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{acq_index}")

        return sched
