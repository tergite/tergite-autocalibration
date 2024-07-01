"""
Module containing a schedule class for Ramsey calibration. (1D parameter sweep, for 2D see ramsey_detunings.py)
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Reset, X
from quantify_scheduler.operations.pulse_library import (
    ResetClockPhase,
    NumericalPulse,
    IdlePulse,
)
from quantify_scheduler.resources import ClockResource
from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.extended_gates import Measure_RO_Opt, Rxy_12
from quantify_scheduler.operations.control_flow_library import Loop
from tergite_autocalibration.config.coupler_config import qubit_types
import numpy as np
import itertools
from tergite_autocalibration.utils.extended_coupler_edge import CompositeSquareEdge
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon


class Reset_calibration_SSRO(BaseMeasurement):
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
        ramsey_phases: dict[str, np.ndarray],
        control_ons: dict[str, np.ndarray],
        repetitions: int = 4096,
        opt_reset_duration_qc: dict[str, float] = None,
        opt_reset_amplitude_qc: dict[str, float] = None,
    ) -> Schedule:
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

        name = "Reset_calibration_ssro"
        schedule = Schedule(f"{name}")

        all_couplers = self.couplers
        all_qubits = [coupler.split(sep="_") for coupler in all_couplers]
        all_qubits = sum(all_qubits, [])
        # print(f'{target = }')
        # print(f'{control = }')

        # The outer for-loop iterates over all qubits:
        shot = Schedule(f"shot")
        shot.add(IdlePulse(16e-9))

        # Initialize ClockResource with the first frequency value
        for this_qubit, this_transmon in self.transmons.items():
            ro_frequency = this_transmon.extended_clock_freqs.readout_3state_opt()
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.ro_3st_opt", freq=ro_frequency)
            )
            mw_frequency_01 = this_transmon.clock_freqs.f01()
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.01", freq=mw_frequency_01)
            )
            mw_frequency_12 = this_transmon.clock_freqs.f12()
            schedule.add_resource(
                ClockResource(name=f"{this_qubit}.12", freq=mw_frequency_12)
            )

        for index, this_coupler in enumerate(all_couplers):
            if this_coupler in ["q21_q22", "q22_q23", "q23_q24", "q24_q25"]:
                downconvert = 0
            else:
                downconvert = 4.4e9
            schedule.add_resource(
                ClockResource(name=f"{this_coupler}.cz", freq=0 + downconvert)
            )
            shot.add_resource(
                ClockResource(name=f"{this_coupler}.cz", freq=0 + downconvert)
            )

        for this_coupler in all_couplers:
            if opt_reset_amplitude_qc is not None:
                reset_amplitude_qc += opt_reset_amplitude_qc[this_coupler]
            if opt_reset_duration_qc is not None:
                reset_duration_qc += opt_reset_duration_qc[this_coupler]

        # print(f'{reset_duration_qc = }')
        # print(f'{reset_amplitude_qc = }')

        ramsey_phases_values = ramsey_phases[all_qubits[0]]
        number_of_phases = len(ramsey_phases_values) + 3  # +3 for calibration points
        control_on_values = control_ons[all_qubits[0]]

        # all_qubits = ['q16','q21']
        state = ["g", "e", "f"]
        states = list(itertools.product(state, state))
        if qubit_types[all_qubits[0]] == "Control":
            all_qubits.reverse()
        test_states = [dict(zip(all_qubits, s)) for s in states]
        for cz_index, control_on in enumerate(control_on_values):
            for ramsey_index, ramsey_phase in enumerate(ramsey_phases_values):
                relaxation = shot.add(
                    Reset(*all_qubits), label=f"Reset_{cz_index}_{ramsey_index}"
                )

                test_state = test_states[int(ramsey_phase)]
                # print(f'{test_state = }')
                for this_qubit in all_qubits:
                    if test_state[this_qubit] == "g":
                        shot.add(IdlePulse(80e-9), ref_op=relaxation, ref_pt="end")
                    elif test_state[this_qubit] == "e":
                        shot.add(IdlePulse(40e-9), ref_op=relaxation, ref_pt="end")
                        shot.add(X(this_qubit))
                    elif test_state[this_qubit] == "f":
                        shot.add(X(this_qubit), ref_op=relaxation, ref_pt="end")
                        shot.add(Rxy_12(this_qubit))

                rep = 1

                if control_on:
                    cz_clock = f"{this_coupler}.cz"
                    cz_pulse_port = f"{this_coupler}:fl"

                    for i in range(rep):
                        buffer = shot.add(IdlePulse(4e-9))
                        # step 1 - calibrate ge/f reset qc pulse

                        fq = 4.50  # qubit frequncy in GHz
                        dt = 1.0  # AWG sampling rate in nanosecond

                        this_coupler = "q22_q23"
                        cz_clock = f"{this_coupler}.cz"
                        cz_pulse_port = f"{this_coupler}:fl"
                        shot.add(ResetClockPhase(clock=this_coupler + ".cz"))
                        f0 = fq + 0.635  # Initial coupler frequency in GHz
                        ft = fq - 0.256  # Final coupler frequency in GJ+Hz
                        g = 0.01288  # = coupling strength
                        duration = 8  # Pulse duration in nanosecond
                        samples = generate_local_adiabatic_fc(
                            g=g, duration=duration, f0=f0, ft=ft, fq=fq, dt=dt
                        )
                        times = np.linspace(0, duration, int(np.ceil(duration / dt)))
                        samples[-2] = samples[-1]
                        qc = shot.add(
                            NumericalPulse(
                                samples=samples,  # Numerical pulses can be complex as well.
                                t_samples=times * 1e-9,
                                port=cz_pulse_port,
                                clock=cz_clock,
                            )
                        )
                        buffer = shot.add(
                            IdlePulse(4e-9),
                            ref_op=buffer,
                            ref_pt="end",
                            rel_time=np.ceil(duration / 4) * 4e-9,
                        )

                buffer_end = shot.add(IdlePulse(4e-9))

                for this_qubit in all_qubits:
                    this_index = cz_index * number_of_phases + ramsey_index
                    # print(f'{this_index = }')
                    shot.add(
                        Measure_RO_Opt(
                            this_qubit, acq_index=this_index, bin_mode=BinMode.APPEND
                        ),
                        ref_op=buffer_end,
                        ref_pt="end",
                    )
                relaxation = shot.add(
                    Reset(*all_qubits), label=f"Reset_End_{cz_index}_{ramsey_index}"
                )

            # Calibration points
            root_relaxation = shot.add(
                Reset(*all_qubits), label=f"Reset_Calib_{cz_index}"
            )

            for this_qubit in all_qubits:
                qubit_levels = range(self.qubit_state + 1)
                number_of_levels = len(qubit_levels)

                shot.add(
                    Reset(*all_qubits), ref_op=root_relaxation, ref_pt_new="end"
                )  # To enforce parallelism we refer to the root relaxation
                # The intermediate for-loop iterates over all ro_amplitudes:
                # for ampl_indx, ro_amplitude in enumerate(ro_amplitude_values):
                # The inner for-loop iterates over all qubit levels:
                for level_index, state_level in enumerate(qubit_levels):
                    calib_index = this_index + level_index + 1
                    # print(f'{calib_index = }')
                    if state_level == 0:
                        prep = shot.add(IdlePulse(40e-9))
                    elif state_level == 1:
                        prep = shot.add(
                            X(this_qubit),
                        )
                    elif state_level == 2:
                        shot.add(
                            X(this_qubit),
                        )
                        prep = shot.add(
                            Rxy_12(this_qubit),
                        )
                    else:
                        raise ValueError("State Input Error")
                    shot.add(
                        Measure_RO_Opt(
                            this_qubit, acq_index=calib_index, bin_mode=BinMode.APPEND
                        ),
                        ref_op=prep,
                        ref_pt="end",
                    )
                    shot.add(Reset(this_qubit))
        shot.add(IdlePulse(16e-9))

        schedule.add(IdlePulse(16e-9))
        schedule.add(shot, control_flow=Loop(repetitions), validate=False)
        # for rep in range(10):
        #     schedule.add(shot, validate=False)
        schedule.add(IdlePulse(16e-9))

        return schedule
