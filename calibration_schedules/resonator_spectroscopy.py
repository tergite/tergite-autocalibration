from quantify_scheduler.enums import BinMode
from quantify_scheduler.schedules.schedule import Schedule
from quantify_scheduler.operations.pulse_library import  SquarePulse, SetClockFrequency, DRAGPulse
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.operations.gate_library import Reset, X, Measure
from quantify_scheduler.resources import ClockResource
# from transmon_element import Measure_1

from calibration_schedules.measurement_base import Measurement
import numpy as np

class Resonator_Spectroscopy(Measurement):

    def __init__(self,transmons,qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.transmons = transmons
        self.static_kwargs = {
            'pulse_amplitudes': self.attributes_dictionary('pulse_amp'),
            'pulse_durations' : self.attributes_dictionary('pulse_duration'),
            'acquisition_delays': self.attributes_dictionary('acq_delay'),
            'integration_times': self.attributes_dictionary('integration_time'),
            # 'mw_ef_amp180s': self.attributes_dictionary('mw_ef_amp180'),
            # 'mw_pulse_durations': self.attributes_dictionary('mw_pulse_duration'),
            # 'mw_clocks_12': self.attributes_dictionary('mw_12_clock'),
            # 'mw_pulse_ports': self.attributes_dictionary('mw_port'),
            # 'freqs_12': self.attributes_dictionary('freq_12'),
            'qubits': self.qubits,
            'ports': self.attributes_dictionary('readout_port'),
        }


    def schedule_function(
        self,
        pulse_amplitudes: dict[str,float],
        pulse_durations: dict[str,float],
        # mw_ef_amp180s: dict[str,float],
        # mw_pulse_durations: dict[str,float],
        # mw_clocks_12: dict[str,str],
        # mw_pulse_ports: dict[str,str],
        # freqs_12:  dict[str,float],
        acquisition_delays: dict[str,float],
        integration_times: dict[str,float],
        qubits: list[str],
        ports: dict[str,str],
        ro_frequencies: dict[str,np.ndarray],
        repetitions: int = 512,
        #TODO re adjust repetions
        ) -> Schedule:

        sched = Schedule("multiplexed_resonator_spectroscopy",repetitions)
        # Initialize the clock for each qubit
        for this_qubit, ro_array_val in ro_frequencies.items():
            #Initialize ClockResource with the first frequency value
            if self.qubit_state==0:
                this_clock = f'{this_qubit}.ro'
            elif self.qubit_state==1:
                this_clock = f'{this_qubit}.ro1'
            sched.add_resource( ClockResource(name=this_clock, freq=ro_array_val[0]) )

        # if self.qubit_state == 2:
        #     for this_qubit, ef_f_val in freqs_12.items():
        #         sched.add_resource( ClockResource( name=mw_clocks_12[this_qubit], freq=ef_f_val) )

        root_relaxation = sched.add(Reset(*qubits), label="Reset")

        # The first for loop iterates over all qubits:
        for acq_cha, (this_qubit, ro_f_values) in enumerate(ro_frequencies.items()):
            # The second for loop iterates over all frequency values in the frequency batch:
            relaxation = root_relaxation
            if self.qubit_state==0:
                this_clock = f'{this_qubit}.ro'
            elif self.qubit_state==1:
                this_clock = f'{this_qubit}.ro1'
            for acq_index, ro_frequency in enumerate(ro_f_values):
                set_frequency = sched.add(
                    SetClockFrequency(clock=this_clock, clock_freq_new=ro_frequency),
                    label=f"set_freq_{this_qubit}_{acq_index}",
                    ref_op=relaxation, ref_pt='end'
                )

                if self.qubit_state == 0:
                    excitation_pulse = set_frequency
                elif self.qubit_state == 1:
                    excitation_pulse = sched.add(X(this_qubit), ref_op=set_frequency, ref_pt='end')
                # elif self.qubit_state == 2:
                #     excitation_pulse_1 = sched.add(X(this_qubit), ref_op=set_frequency, ref_pt='end')
                #     excitation_pulse = sched.add(
                #         DRAGPulse(
                #             duration=mw_pulse_durations[this_qubit],
                #             G_amp=mw_ef_amp180s[this_qubit],
                #             D_amp=0,
                #             port=mw_pulse_ports[this_qubit],
                #             clock=mw_clocks_12[this_qubit],
                #             phase=0,
                #         ),
                #         label=f"rabi_pulse_{this_qubit}_{acq_index}", ref_op=excitation_pulse_1, ref_pt="end",
                #     )

                pulse = sched.add(
                    SquarePulse(
                        duration=pulse_durations[this_qubit],
                        amp=pulse_amplitudes[this_qubit],
                        port=ports[this_qubit],
                        clock=this_clock,
                    ),
                )

                sched.add(
                    SSBIntegrationComplex(
                        duration=integration_times[this_qubit],
                        port=ports[this_qubit],
                        clock=this_clock,
                        acq_index=acq_index,
                        acq_channel=acq_cha,
                        bin_mode=BinMode.AVERAGE
                    ),
                    ref_op=pulse, ref_pt="start",
                    rel_time=acquisition_delays[this_qubit],
                    label=f"acquisition_{this_qubit}_{acq_index}",
                )

                #sched.add(
                #    Measure(this_qubit, acq_index=acq_index, acq_channel=acq_cha, bin_mode=BinMode.AVERAGE),
                #    label=f'Measurement_{this_qubit}_{acq_index}',
                #    ref_op=excitation_pulse,
                #    ref_pt="end",
                #)

                # update the relaxation for the next batch point
                relaxation = sched.add(Reset(this_qubit), label=f"Reset_{this_qubit}_{acq_index}")

        return sched
