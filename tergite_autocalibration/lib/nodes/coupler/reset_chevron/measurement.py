"""
Module containing a schedule class for Ramsey calibration. (1D parameter sweep, for 2D see ramsey_detunings.py)
"""
import numpy as np
from quantify_scheduler import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X, CZ
from quantify_scheduler.operations.pulse_library import (
    GaussPulse,
    SuddenNetZeroPulse,
    ResetClockPhase,
    IdlePulse,
    DRAGPulse,
    SetClockFrequency,
    NumericalPulse,
    SoftSquarePulse,
    SquarePulse,
)
from quantify_scheduler.operations.pulse_library import (
    RampPulse,
    DRAGPulse,
    SetClockFrequency,
    NumericalPulse,
    SoftSquarePulse,
    SquarePulse,
    ResetClockPhase,
)
from quantify_scheduler.resources import ClockResource

from tergite_autocalibration.utils.extended_coupler_edge import CompositeSquareEdge
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon
from tergite_autocalibration.utils.extended_gates import Measure_RO1, Rxy_12
from ....base.measurement import BaseMeasurement
from tergite_autocalibration.config.coupler_config import edge_group, qubit_types


class Reset_Chevron_DC(BaseMeasurement):
    # for testing dc reset

    def __init__(
        self,
        transmons: dict[str, ExtendedTransmon],
        couplers: dict[str, CompositeSquareEdge],
        qubit_state: int = 0,
    ):
        super().__init__(transmons)
        self.transmons = transmons
        self.qubit_state = qubit_state
        self.couplers = couplers

    def schedule_function(
        self,
        reset_pulse_amplitudes: dict[str, np.ndarray],
        reset_pulse_durations: dict[str, np.ndarray],
        repetitions: int = 1024,
    ) -> Schedule:
        """
        Generate a schedule for performing a Ramsey fringe measurement on multiple qubits.
        Can be used both to finetune the qubit frequency and to measure the qubit dephasing time T_2. (1D parameter sweep)

        Schedule sequence
            Reset -> pi/2-pulse -> Idle(tau) -> pi/2-pulse -> Measure

        Parameters
        ----------
        self
            Contains all qubit states.
        qubits
            A list of two qubits to perform the experiment on. i.e. [['q1','q2'],['q3','q4'],...]
        mw_clocks_12
            Clocks for the 12 transition frequency of the qubits.
        mw_ef_amps180
            Amplitudes used for the excitation of the qubits to calibrate for the 12 transition.
        mw_frequencies_12
            Frequencies used for the excitation of the qubits to calibrate for the 12 transition.
        mw_pulse_ports
            Location on the device where the pulsed used for excitation of the qubits to calibrate for the 12 transition is located.
        mw_pulse_durations
            Pulse durations used for the excitation of the qubits to calibrate for the 12 transition.
        cz_pulse_frequency
            The frequency of the CZ pulse.
        cz_pulse_amplitude
            The amplitude of the CZ pulse.
        cz_pulse_duration
            The duration of the CZ pulse.
        cz_pulse_width
            The width of the CZ pulse.
        testing_group
            The edge group to be tested. 0 means all edges.
        repetitions
            The amount of times the Schedule will be repeated.

        Returns
        -------
        :
            An experiment schedule.
        """

        def local_analytic(t, a, g, c):
            numerator = -8 * g * (a * g * t + c)
            denominator = np.sqrt(
                abs(1 - 16 * (a * g * t) ** 2 - 32 * a * g * t * c - 16 * c**2)
            )
            y = numerator / denominator
            return y

        def generate_local_adiabatic_pulse(g, T, y0, yt, dt=0.1):
            c = -y0 / np.sqrt(64 * g**2 + 16 * y0**2)
            a = (
                -4 * c * (4 * g**2 + yt**2) - yt * np.sqrt(4 * g**2 + yt**2)
            ) / (4 * g * T * (4 * g**2 + yt**2))
            # times = np.arange(0, T, dt)
            times = np.linspace(0, T, int(np.ceil(T / dt)))
            seq = local_analytic(times, a, g, c)

            return seq

        def generate_local_adiabatic_fc(g, duration, f0, ft, fq, dt=1.0):
            y0 = fq - f0
            yt = fq - ft
            seq_fq_fc_detuning = generate_local_adiabatic_pulse(
                g, duration, y0, yt, dt=dt
            )
            seq_fc_f0_detuning = -seq_fq_fc_detuning + fq - f0

            return seq_fc_f0_detuning * 1e-1

        schedule = Schedule("reset_chevron", repetitions)
        coupler = list(self.couplers.keys())[0]
        qubits = coupler.split(sep="_")

        # cz_frequency_values = np.array(list(cz_pulse_frequencies_sweep.values())[0])
        reset_duration_values = list(reset_pulse_durations.values())[0]
        reset_pulse_amplitude_values = list(reset_pulse_amplitudes.values())[0]
        # print(f'{ reset_duration_values = }')
        # print(f'{ reset_pulse_amplitude_values = }')

        # print(f'{ cz_frequency_values[0] = }')

        # schedule.add_resource(
        #     ClockResource(name=coupler+'.cz',freq= - cz_frequency_values[0] + 4.4e9)
        # )

        # schedule.add_resource(
        #     ClockResource(name=coupler+'.cz',freq= 4.4e9)
        # )

        # schedule.add_resource(
        #     ClockResource(name=coupler+'.cz',freq= 0e9)
        # )

        all_couplers = ["q21_q22", "q22_q23", "q23_q24", "q24_q25"]
        for index, this_coupler in enumerate(all_couplers):
            if this_coupler in ["q21_q22", "q22_q23", "q23_q24", "q24_q25"]:
                downconvert = 0
            else:
                downconvert = 4.4e9
            schedule.add_resource(
                ClockResource(name=f"{this_coupler}.cz", freq=0 + downconvert)
            )

        number_of_durations = len(reset_duration_values)

        # The outer loop, iterates over all cz_frequencies
        for freq_index, reset_amplitude in enumerate(reset_pulse_amplitude_values):
            cz_clock = f"{coupler}.cz"
            cz_pulse_port = f"{coupler}:fl"
            # schedule.add(
            #     SetClockFrequency(clock=cz_clock, clock_freq_new= - cz_frequency + 4.4e9),
            # )
            # schedule.add(
            #     SetClockFrequency(clock=cz_clock, clock_freq_new=4.4e9),
            # )

            # The inner for loop iterates over cz pulse durations
            for acq_index, reset_duration in enumerate(reset_duration_values):
                this_index = freq_index * number_of_durations + acq_index

                relaxation = schedule.add(Reset(*qubits))

                for this_qubit in qubits:
                    if qubit_types[this_qubit] == "Target":
                        # schedule.add(Rxy(0,0,this_qubit), ref_op=relaxation, ref_pt='end')
                        # schedule.add(X(this_qubit))
                        schedule.add(X(this_qubit), ref_op=relaxation, ref_pt="end")
                        schedule.add(Rxy_12(this_qubit, 90, 0))
                    else:
                        # schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                        # schedule.add(Rxy_12(this_qubit,90,0))
                        schedule.add(
                            Rxy(0, 0, this_qubit), ref_op=relaxation, ref_pt="end"
                        )
                        # schedule.add(Rxy(0,0,this_qubit))
                        schedule.add(X(this_qubit))

                for i in range(1):
                    # step 1 - calibrate ge/f reset qc pulse

                    buffer = schedule.add(IdlePulse(4e-9))

                    qc = schedule.add(
                        RampPulse(
                            # offset = -0.4,
                            duration=reset_duration,
                            amp=-reset_amplitude,
                            offset=reset_amplitude,
                            # amp = 0.,
                            port=cz_pulse_port,
                            clock=cz_clock,
                        ),
                        # SquarePulse(
                        #     duration=reset_duration,
                        #     amp = reset_amplitude,
                        #     port=cz_pulse_port,
                        #     clock=cz_clock,
                        # ),
                    )

                    buffer = schedule.add(
                        IdlePulse(4e-9),
                        ref_op=buffer,
                        ref_pt="end",
                        rel_time=np.ceil(reset_duration * 1e9 / 4) * 4e-9,
                    )

                    # for this_qubit in qubits:
                    #     if qubit_types[this_qubit] == 'Target':
                    #         schedule.add(Rxy(0,0,this_qubit), ref_op=buffer, ref_pt='end')
                    #     else:
                    #         schedule.add(X(this_qubit), ref_op=buffer, ref_pt='end')
                    # buffer = schedule.add(IdlePulse(np.ceil( reset_duration* 1e9 / 4) * 4e-9))

                ########################################################################################################################################################
                # reset_duration_qc = 49e-9
                # reset_amplitude_qc = -0.145
                # qc = schedule.add(
                #             RampPulse(
                #                 # offset = -0.4,
                #                 duration = reset_duration_qc,
                #                 amp = -reset_amplitude_qc,
                #                 offset = reset_amplitude_qc,
                #                 # amp = 0.,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc * 1e9 / 4) * 4e-9)

                # reset_amplitude_cr = 0.19
                # reset_duration_cr = 27e-9

                # cr = schedule.add(
                #             RampPulse(
                #                 offset = reset_amplitude_cr,
                #                 duration = reset_duration_cr,
                #                 amp = -reset_amplitude_cr,
                #                 # amp = 0.,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_cr/ 4) * 4e-9)

                # qc = schedule.add(
                #             RampPulse(
                #                 # offset = -0.4,
                #                 duration = reset_duration,
                #                 amp = -reset_amplitude,
                #                 offset = reset_amplitude,
                #                 # amp = 0.,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)

                ########################################################################################################################################################

                # fq = 4.50  # qubit frequncy in GHz
                # dt = 1.0  # AWG sampling rate in nanosecond

                # q23_q24

                # # sweep f0, t
                # e
                # f0 = fq+reset_amplitude# Initial coupler frequency in GHz
                # ft = fq-0.195# Final coupler frequency in GJ+Hz
                # g = 0.0415  # = coupling strength
                # duration = (reset_duration)*1e9  # Pulse duration in nanosecond
                # f
                # f0 = fq+reset_amplitude# Initial coupler frequency in GHz
                # ft = fq-0.2175# Final coupler frequency in GJ+Hz
                # g = 0.06750  # = coupling strength
                # duration = (reset_duration)*1e9  # Pulse duration in nanosecond

                # sweep g, ft
                # e
                # f0 = 4.50+0.935 # Initial coupler frequency in GHz
                # ft = fq+reset_amplitude# Final coupler frequency in GJ+Hz
                # g = reset_duration  # = coupling strength
                # duration = 40  # Pulse duration in nanosecond
                # f
                # f0 = fq+1.04 # Initial coupler frequency in GHz
                # ft = fq+reset_amplitude# Final coupler frequency in GJ+Hz
                # g = reset_duration  # = coupling strength
                # duration = 61  # Pulse duration in nanosecond

                # fixed qc
                # e
                # f0 = 4.50+0.933 # Initial coupler frequency in GHz
                # ft = fq-0.233# Final coupler frequency in GJ+Hz
                # g = 0.05  # = coupling strength
                # duration = 9  # Pulse duration in nanosecond
                # f
                # f0 = fq+1.04 # Initial coupler frequency in GHz
                # ft = fq-0.24# Final coupler frequency in GJ+Hz
                # g = 0.08  # = coupling strength
                # duration = 61  # Pulse duration in nanosecond

                # this_coupler = 'q23_q24'
                # cz_clock = f'{this_coupler}.cz'
                # cz_pulse_port = f'{this_coupler}:fl'
                # schedule.add(ResetClockPhase(clock=coupler+'.cz'))
                # buffer = schedule.add(IdlePulse(4e-9))
                # samples = generate_local_adiabatic_fc(g=g, duration=duration, f0=f0, ft=ft, fq=fq, dt=dt)
                # times = np.linspace(0, duration, int(np.ceil(duration / dt)))
                # samples[-2] = samples[-1]
                # qc = schedule.add(
                #     NumericalPulse(
                #         samples=samples,  # Numerical pulses can be complex as well.
                #         t_samples=times*1e-9,
                #         port = cz_pulse_port,
                #         clock = cz_clock,
                #     )
                # )
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( duration / 4) * 4e-9)

                ########################################################################################################################################################
                # q22_q23
                # sweep f0, t
                # e
                # f0 = fq+reset_amplitude# Initial coupler frequency in GHz
                # ft = fq-0.2 # Final coupler frequency in GJ+Hz
                # g = 0.04  # = coupling strength
                # duration = (reset_duration)*1e9  # Pulse duration in nanosecond
                # f
                # f0 = fq+reset_amplitude# Initial coupler frequency in GHz
                # ft = fq-0.21 # Final coupler frequency in GJ+Hz
                # g = 0.067  # = coupling strength
                # duration = (reset_duration)*1e9  # Pulse duration in nanosecond

                # sweep g, ft
                # e
                # f0 = fq+0.635 # Ini1tial coupler frequency in GHz
                # ft = fq+reset_amplitude# Final coupler frequency in GJ+Hz
                # g = reset_duration  # = coupling strength
                # duration = 8  # Pulse duration in nanosecond
                # f
                # f0 = fq+0.77161 # Ini1tial coupler frequency in GHz
                # ft = fq+reset_amplitude# Final coupler frequency in GJ+Hz
                # g = reset_duration  # = coupling strength
                # duration = 64  # Pulse duration in nanosecond

                # fixed
                # f0 = fq+0.635 # Initial coupler frequency in GHz
                # ft = fq-0.256# Final coupler frequency in GJ+Hz
                # g = 0.01288  # = coupling strength
                # duration = 8  # Pulse duration in nanosecond
                # f
                # f0 = fq+0.77161 # Initial coupler frequency in GHz
                # ft = fq-0.215# Final coupler frequency in GJ+Hz
                # g = 0.07  # = coupling strength
                # duration = 64  # Pulse duration in nanosecond

                # this_coupler = 'q22_q23'
                # cz_clock = f'{this_coupler}.cz'
                # cz_pulse_port = f'{this_coupler}:fl'
                # schedule.add(ResetClockPhase(clock=this_coupler+'.cz'))
                # buffer = schedule.add(IdlePulse(4e-9))
                # samples = generate_local_adiabatic_fc(g=g, duration=duration, f0=f0, ft=ft, fq=fq, dt=dt)
                # times = np.linspace(0, duration, int(np.ceil(duration / dt)))
                # samples[-2] = samples[-1]
                # qc = schedule.add(
                #     NumericalPulse(
                #         samples=samples,  # Numerical pulses can be complex as well.
                #         t_samples=times*1e-9,
                #         port = cz_pulse_port,
                #         clock = cz_clock,
                #     )
                # )
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( duration / 4) * 4e-9)

                ########################################################################################################################################################

                # q23_q24
                # this_coupler = 'q23_q24'
                # cz_clock = f'{this_coupler}.cz'
                # cz_pulse_port = f'{this_coupler}:fl'
                # schedule.add(ResetClockPhase(clock=coupler+'.cz'))

                # reset_amplitude_qc = -0.096
                # reset_duration_qc = 7e-9

                # buffer = schedule.add(IdlePulse(4e-9))
                # qc = schedule.add(
                #             RampPulse(
                #                 offset = reset_amplitude_qc,
                #                 duration = reset_duration_qc,
                #                 amp = 0,
                #                 # amp = 0.,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc / 4) * 4e-9)

                # fr = 6.5 # qubit frequncy in GHz
                # dt = 1.0  # AWG sampling rate in nanosecond

                # sweep f0, t
                # f0 = fr + 0.3# Initial coupler frequency in GHz
                # ft = fr - reset_amplitude # Final coupler frequency in GJ+Hz
                # g = 0.06  # = coupling strength
                # duration = (reset_duration)*1e9  # Pulse duration in nanosecond

                # sweep g, ft
                # f0 = fr+0.635 # Ini1tial coupler frequency in GHz
                # ft = fr+reset_amplitude# Final coupler frequency in GJ+Hz
                # g = reset_duration  # = coupling strength
                # duration = 8  # Pulse duration in nanosecond

                # fixed cr
                # f0 = fr + 1.45 # Initial coupler frequency in GHz
                # ft = fr - 1.0 # Final coupler frequency in GJ+Hz
                # g = 0.120  # = coupling strength
                # duration = 7  # Pulse duration in nanosecond

                # reset_amplitude_cr = 0.19
                # reset_duration_cr = 27e-9

                # cr = schedule.add(
                #             RampPulse(
                #                 offset = reset_amplitude,
                #                 duration = reset_duration,
                #                 amp = -reset_amplitude,
                #                 # amp = 0.,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration/ 4) * 4e-9)

                # samples = generate_local_adiabatic_fc(g=g, duration=duration, f0=f0, ft=ft, fq=fq, dt=dt)
                # times = np.linspace(0, duration, int(np.ceil(duration / dt)))
                # samples[-2] = samples[-1]
                # samples = samples + max(abs(samples))
                # cr = schedule.add(
                #     NumericalPulse(
                #         samples=samples,  # Numerical pulses can be complex as well.
                #         t_samples=times*1e-9,
                #         port = cz_pulse_port,
                #         clock = cz_clock,
                #     )
                # )
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( duration / 4) * 4e-9)

                # qc = schedule.add(
                #             RampPulse(
                #                 offset = reset_amplitude_qc,
                #                 duration = reset_duration_qc,
                #                 amp = 0,
                #                 # amp = 0.,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc / 4) * 4e-9)

                # # sweep ft
                # fq = 6.5 # qubit frequncy in GHz
                # f0 = fq+0.5 # Initial coupler frequency in GHz
                # ft = fq - reset_amplitude # Final coupler frequency in GJ+Hz
                # g = 0.06  # = coupling strength
                # duration = reset_duration*1e9  # Pulse duration in nanosecond
                # dt = 1.0  # AWG sampling rate in nanosecond

                # sweep g,f0
                # fq = 6.5 # qubit frequncy in GHz
                # f0 = fq+reset_amplitude # Initial coupler frequency in GHz
                # ft = fq - 1.0 # Final coupler frequency in GJ+Hz
                # g = reset_duration  # = coupling strength
                # duration = 7  # Pulse duration in nanosecond
                # dt = 1.0  # AWG sampling rate in nanosecond

                # fixed cr
                # fq = 6.5 # qubit frequncy in GHz
                # f0 = fq + 1.45 # Initial coupler frequency in GHz
                # ft = fq - 1.0 # Final coupler frequency in GJ+Hz
                # g = 0.120  # = coupling strength
                # duration = 7  # Pulse duration in nanosecond
                # dt = 1.0  # AWG sampling rate in nanosecond

                # samples = generate_local_adiabatic_fc(g=g, duration=duration, f0=f0, ft=ft, fq=fq, dt=dt)
                # times = np.linspace(0, duration, int(np.ceil(duration / dt)))
                # samples[-2] = samples[-1]
                # samples = samples + max(abs(samples))
                # cr = schedule.add(
                #     NumericalPulse(
                #         samples=samples,  # Numerical pulses can be complex as well.
                #         t_samples=times*1e-9,
                #         port = cz_pulse_port,
                #         clock = cz_clock,
                #     )
                # )
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( duration / 4) * 4e-9)

                # cr = schedule.add(
                #             RampPulse(
                #                 offset = reset_amplitude,
                #                 duration = reset_duration,
                #                 amp = 0,
                #                 # amp = 0.,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration * 1e9 / 4) * 4e-9)

                # reset_amplitude_qc = -0.084
                # reset_duration_qc = 16e-9
                # qc = schedule.add(
                #             RampPulse(
                #                 offset = reset_amplitude_qc,
                #                 duration = reset_duration_qc,
                #                 amp = 0,
                #                 # amp = 0.,
                #                 port = cz_pulse_port,
                #                 clock = cz_clock,
                #             ),
                #         )

                # # qc = schedule.add(
                # #             RampPulse(
                # #                 offset = reset_amplitude,
                # #                 duration = reset_duration,
                # #                 amp = 0,
                # #                 # amp = 0.,
                # #                 port = cz_pulse_port,
                # #                 clock = cz_clock,
                # #             ),
                # #         )
                # buffer = schedule.add(IdlePulse(4e-9),ref_op=buffer, ref_pt='end',rel_time = np.ceil( reset_duration_qc * 1e9 / 4) * 4e-9)

                buffer_end = schedule.add(IdlePulse(4e-9))

                for this_qubit in qubits:
                    schedule.add(
                        Measure(
                            this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE
                        ),
                        ref_op=buffer_end,
                        ref_pt="end",
                    )

        return schedule
