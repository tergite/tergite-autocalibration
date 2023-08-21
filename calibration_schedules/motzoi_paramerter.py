from quantify_scheduler.resources import ClockResource
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.operations.gate_library import Measure, Reset
from calibration_schedules.measurement_base import Measurement

class Motzoi_parameter(Measurement):

    def __init__(self,transmons):
        super().__init__(transmons)
        self.transmons = transmons
        self.static_kwargs = {
            'qubits': self.qubits,
            'mw_frequencies': self.attributes_dictionary('f01'),
            'mw_amplitudes': self.attributes_dictionary('mw_amp180'),
            'mw_pulse_durations': self.attributes_dictionary('duration'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
        }

    def schedule_function(
            self,
            qubits: list[str],
            mw_frequencies: dict[str,float],
            mw_amplitudes: dict[str,float],
            mw_pulse_ports: dict[str,str],
            mw_pulse_durations: dict[str,float],
            mw_motzois: dict[str,np.ndarray],
            X_repetitions: dict[str,np.ndarray],
            repetitions: int = 1024,
        ) -> Schedule:
        schedule = Schedule("mltplx_motzoi",repetitions)

        for this_qubit, mw_f_val in mw_frequencies.items():
            schedule.add_resource(
                ClockResource( name=f'{this_qubit}.01', freq=mw_f_val)
            )

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer loop, iterates over all qubits
        for acq_cha, (this_qubit, X_values) in enumerate(X_repetitions.items()):

            motzoi_parameter_values = mw_motzois[this_qubit]
            number_of_motzois = len(motzoi_parameter_values)

            # The second for loop iterates over all frequency values in the frequency batch:
            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            for motzoi_index, mw_motzoi in enumerate(motzoi_parameter_values):
                for x_index in range(X_values):
                    schedule.add(
                        DRAGPulse(
                            duration=mw_pulse_durations[this_qubit],
                            G_amp=mw_amplitudes[this_qubit],
                            D_amp=mw_motzoi,
                            port=mw_pulse_ports[this_qubit],
                            clock=mw_clocks[this_qubit],
                            phase=0,
                        ),
                        label=f"motzoi_drag_pulse_{this_qubit}_{x_index}_{acq_index}",
                    )
                    # inversion pulse requires 180 deg phase
                    schedule.add(
                        DRAGPulse(
                            duration=mw_pulse_durations[this_qubit],
                            G_amp=mw_amplitudes[this_qubit],
                            D_amp=mw_motzoi,
                            port=mw_pulse_ports[this_qubit],
                            clock=mw_clocks[this_qubit],
                            phase=180,
                        ),
                        label=f"motzoi_inverse_drag_pulse_{this_qubit}_{x_index}_{acq_index}",
                    )

                schedule.add(
                    Measure(this_qubit, acq_channel=acq_cha, acq_index=acq_index),
                    label=f"Measurement_{acq_index}_{acq_cha}_{this_qubit}"
                )

                schedule.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{acq_index}")

        return schedule
