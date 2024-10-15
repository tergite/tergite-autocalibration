# pylint: disable=invalid-name, protected-access
"""
Provides utilities for mixer calibration
"""
import numpy as np
import cma


def _amp_ratio_phase_from_IQ(z_minus, z_plus):
    """
    Given I and Q values at -freq and +freq,
    and assuming the input at that frequency is a pure sine wave,
    solve for Amplitude of sine, phase of sine,
    amp_ratio and phase_offset of the input mixer.
    """
    I_minus = z_minus.real
    Q_minus = z_minus.imag
    I_plus = z_plus.real
    Q_plus = z_plus.imag

    amp = ((I_minus + I_plus) ** 2 + (Q_plus - Q_minus) ** 2) ** 0.5
    phase = np.angle((I_minus + I_plus) + 1j * (Q_plus - Q_minus))
    amp_ratio = (((I_plus - I_minus) ** 2 + (Q_plus + Q_minus) ** 2) / amp ** 2) ** 0.5
    phase_offset = np.angle(
        np.exp(1j * -phase) * ((I_plus - I_minus) + 1j * (Q_minus + Q_plus))
    )

    return amp, phase, amp_ratio, phase_offset


class _LeakageCalibrationContextManager:
    def __init__(
        self,
        cal_module,
        cal_output,
        input_module,
        lo_freq=None,
        input_sequencer=0,
        input_sequencer2=1,
        lo_mismatch=77e6,
        verbose=True,
    ):
        self.cal_module = cal_module
        self.cal_output = cal_output
        self.input_module = input_module
        self.lo_freq = lo_freq
        if input_sequencer == input_sequencer2:
            raise ValueError(
                "'input_sequencer' cannot be the same as 'input_sequencer2'."
            )
        self.input_sequencer = input_sequencer
        self.input_sequencer2 = input_sequencer2
        self.lo_mismatch = lo_mismatch
        self.verbose = verbose

    def __enter__(self):
        for module in self.cal_module.parent.modules:
            try:
                for sequencer in module.sequencers:
                    sequencer.sync_en(False)
            except AttributeError:
                pass
        if self.cal_module.parent is not self.input_module.parent:
            for module in self.input_module.parent.modules:
                try:
                    for sequencer in module.sequencers:
                        sequencer.sync_en(False)
                except AttributeError:
                    pass

        if self.cal_module.is_qrm_type:
            out_lo_param = self.cal_module.out0_in0_lo_freq
            marker_override_value = 2
            out_lo_enable_param = self.cal_module.parameters[
                f"out{self.cal_output}_in{self.cal_output}_lo_en"
            ]

        else:
            out_lo_param = self.cal_module.parameters[f"out{self.cal_output}_lo_freq"]
            out_lo_enable_param = self.cal_module.parameters[
                f"out{self.cal_output}_lo_en"
            ]
            marker_override_value = 2 ** self.cal_output

        if self.lo_freq is not None:
            out_lo_param(self.lo_freq)
        else:
            self.lo_freq = out_lo_param()

        if self.cal_module is self.input_module:
            assert self.input_module.is_qrm_type

            self.input_module.parent._write(
                f"SLOT{self.input_module._slot_idx}:LO:SH:ENA 0"
            )

            self.input_module._set_lo_enable_0(True)
            self.input_module._set_lo_freq_0(int(self.lo_freq + self.lo_mismatch))
        else:
            self.input_module.parent._write(
                f"SLOT{self.input_module._slot_idx}:LO:SH:ENA 1"
            )

            out_lo_enable_param(True)
            self.input_module.out0_in0_lo_freq(self.lo_freq + self.lo_mismatch)
        self.input_module.out0_in0_lo_en(True)

        input_seq = self.input_module[f"sequencer{self.input_sequencer}"]
        input_seq2 = self.input_module[f"sequencer{self.input_sequencer2}"]

        integration_length = 60000
        num_bins = 100

        input_seq.marker_ovr_en(True)
        input_seq.marker_ovr_value(1)  # Enables input on QRM-RF
        input_seq.mod_en_awg(True)
        input_seq.demod_en_acq(True)
        input_seq.nco_freq(-self.lo_mismatch)
        input_seq.integration_length_acq(integration_length)
        input_seq.sync_en(True)

        input_seq2.mod_en_awg(True)
        input_seq2.demod_en_acq(True)
        input_seq2.nco_freq(self.lo_mismatch)
        input_seq2.integration_length_acq(integration_length)
        input_seq2.sync_en(True)

        self.cal_module.sequencer0.marker_ovr_en(True)
        self.cal_module.sequencer0.sync_en(False)
        self.cal_module.sequencer0.marker_ovr_value(
            marker_override_value
        )  # Enables output on QRM-RF

        leakage_input_seq_program = f"""
        wait_sync   4
        move 0, R0
        nop
        loop:
            acquire 0,R0,{integration_length}
            add     R0, 1, R0
            nop
            jlt     R0, {num_bins}, @loop
        stop
        """
        acquisitions = {"acq": {"num_bins": num_bins, "index": 0}}

        # Add sequence to single dictionary and write to JSON file.
        sequence = {
            "waveforms": {},
            "weights": {},
            "acquisitions": acquisitions,
            "program": leakage_input_seq_program,
        }

        # Upload sequence
        input_seq.sequence(sequence)
        input_seq2.sequence(sequence)

        def get_data_qrm_rf():
            input_seq.delete_acquisition_data("acq")
            input_seq2.delete_acquisition_data("acq")

            input_seq.arm_sequencer()
            input_seq2.arm_sequencer()
            self.input_module.parent.start_sequencer()

            # Wait for the sequencer to stop with a timeout period of one minute.
            self.input_module.get_acquisition_status(self.input_sequencer, timeout=1)
            self.input_module.get_acquisition_status(self.input_sequencer2, timeout=1)

            ########## Integrated number #################
            data = self.input_module.get_acquisitions(self.input_sequencer)
            I = np.array(data["acq"]["acquisition"]["bins"]["integration"]["path0"])
            Q = np.array(data["acq"]["acquisition"]["bins"]["integration"]["path1"])

            data = self.input_module.get_acquisitions(self.input_sequencer2)
            I2 = np.array(data["acq"]["acquisition"]["bins"]["integration"]["path0"])
            Q2 = np.array(data["acq"]["acquisition"]["bins"]["integration"]["path1"])

            amp, _, _, _ = _amp_ratio_phase_from_IQ(I + 1j * Q, I2 + 1j * Q2)

            return np.sum(amp)

        def leakage_func(params, verbose):
            result = []
            for off1, off2 in params:
                getattr(self.cal_module, f"out{self.cal_output}_offset_path0")(off1)
                getattr(self.cal_module, f"out{self.cal_output}_offset_path1")(off2)

                result.append(get_data_qrm_rf())

            if verbose:
                print(f"Calibrating leakage: LO power = {np.min(result)}", end="\r")
            return result

        return lambda params: leakage_func(params, verbose=self.verbose)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.input_module._set_lo_enable_0(False)
        self.input_module.parent._write(
            f"SLOT{self.input_module._slot_idx}:LO:SH:ENA 1"
        )


class _SidebandCalibrationContextManager:
    def __init__(
        self,
        cal_module,
        cal_output,
        input_module,
        cal_freq=None,
        lo_freq=None,
        cal_sequencer=2,
        input_sequencer=0,
        input_sequencer2=1,
        lo_mismatch=77e6,
        verbose=True,
    ):
        self.cal_module = cal_module
        self.cal_output = cal_output
        self.input_module = input_module
        self.cal_freq = cal_freq
        self.lo_freq = lo_freq
        self.cal_sequencer = cal_sequencer
        if input_sequencer == input_sequencer2:
            raise ValueError(
                "'input_sequencer' cannot be the same as 'input_sequencer2'."
            )
        self.input_sequencer = input_sequencer
        self.input_sequencer2 = input_sequencer2
        self.lo_mismatch = lo_mismatch
        self.verbose = verbose

    def __enter__(self):
        for module in self.cal_module.parent.modules:
            try:
                for sequencer in module.sequencers:
                    sequencer.sync_en(False)
            except AttributeError:
                pass
        if self.cal_module.parent is not self.input_module.parent:
            for module in self.input_module.parent.modules:
                try:
                    for sequencer in module.sequencers:
                        sequencer.sync_en(False)
                except AttributeError:
                    pass

        if self.cal_module.is_qrm_type:
            out_lo_param = self.cal_module.out0_in0_lo_freq
            marker_override_value = 2
        else:
            out_lo_param = self.cal_module.parameters[f"out{self.cal_output}_lo_freq"]
            marker_override_value = 2 ** self.cal_output

        if self.lo_freq is not None:
            out_lo_param(self.lo_freq)
        else:
            self.lo_freq = out_lo_param()

        input_seq = self.input_module[f"sequencer{self.input_sequencer}"]
        input_seq2 = self.input_module[f"sequencer{self.input_sequencer2}"]
        cal_seq = self.cal_module[f"sequencer{self.cal_sequencer}"]

        if self.cal_freq is not None:
            delta = self.cal_freq - self.lo_freq
            cal_seq.nco_freq(delta)
        else:
            delta = cal_seq.nco_freq()
            self.cal_freq = self.lo_freq + delta

        if self.cal_module is self.input_module:
            if self.input_sequencer == self.cal_sequencer:
                raise ValueError(
                    "'input_sequencer' cannot be the same as 'cal_sequencer'."
                )
            assert (
                self.input_module.is_qrm_type
            ), "You can only calibrate a module with itself if it is a QRM-RF."

            self.input_module.parent._write(
                f"SLOT{self.input_module._slot_idx}:LO:SH:ENA 0"
            )

            self.input_module._set_lo_enable_0(True)
            self.input_module._set_lo_freq_0(
                int(self.lo_freq - delta + self.lo_mismatch)
            )
        else:
            self.input_module.parent._write(
                f"SLOT{self.input_module._slot_idx}:LO:SH:ENA 1"
            )
            if self.cal_module.is_qrm_type:
                self.cal_module.parameters[
                    f"out{self.cal_output}_in{self.cal_output}_lo_en"
                ](True)
            else:
                self.cal_module.parameters[f"out{self.cal_output}_lo_en"](True)
            self.input_module.out0_in0_lo_freq(self.lo_freq - delta + self.lo_mismatch)
        self.input_module.out0_in0_lo_en(True)

        integration_length = 60000
        num_bins = 100

        input_seq.marker_ovr_en(True)
        input_seq.marker_ovr_value(1)
        input_seq.mod_en_awg(True)
        input_seq.demod_en_acq(True)
        input_seq.nco_freq(-self.lo_mismatch)
        input_seq.integration_length_acq(integration_length)
        input_seq.sync_en(True)

        input_seq2.mod_en_awg(True)
        input_seq2.demod_en_acq(True)
        input_seq2.nco_freq(self.lo_mismatch)
        input_seq2.integration_length_acq(integration_length)
        input_seq2.sync_en(True)

        cal_seq.marker_ovr_en(True)
        cal_seq.marker_ovr_value(marker_override_value)
        cal_seq.mod_en_awg(True)
        cal_seq.sync_en(True)

        amp_phase_cal_seq_program = """
        wait_sync   4
        set_awg_offs 10000, 0
        upd_param    4
        stop
        """

        sequence = {
            "waveforms": {},
            "weights": {},
            "acquisitions": {},
            "program": amp_phase_cal_seq_program,
        }

        # Upload sequence
        cal_seq.sequence(sequence)

        amp_phase_input_seq_program = f"""
        wait_sync   4
        move 0, R0
        nop
        loop:
            acquire 0,R0,{integration_length}
            add     R0, 1, R0
            nop
            jlt     R0, {num_bins}, @loop
        stop
        """
        acquisitions = {"acq": {"num_bins": 100, "index": 0}}

        # Add sequence to single dictionary and write to JSON file.
        sequence = {
            "waveforms": {},
            "weights": {},
            "acquisitions": acquisitions,
            "program": amp_phase_input_seq_program,
        }

        # Upload sequence
        input_seq.sequence(sequence)
        input_seq2.sequence(sequence)

        def get_data_qrm_rf():
            input_seq.delete_acquisition_data("acq")
            input_seq2.delete_acquisition_data("acq")

            cal_seq.arm_sequencer()
            input_seq.arm_sequencer()
            input_seq2.arm_sequencer()
            if self.cal_module.parent is self.input_module.parent:
                self.input_module.parent.start_sequencer()
            else:
                self.cal_module.parent.start_sequencer()
                self.input_module.parent.start_sequencer()

            # Wait for the sequencer to stop with a timeout period of one minute.
            self.input_module.get_acquisition_status(self.input_sequencer, timeout=1)
            self.input_module.get_acquisition_status(self.input_sequencer2, timeout=1)

            ########## Integrated number #################
            data = self.input_module.get_acquisitions(self.input_sequencer)
            I = np.array(data["acq"]["acquisition"]["bins"]["integration"]["path0"])
            Q = np.array(data["acq"]["acquisition"]["bins"]["integration"]["path1"])

            data = self.input_module.get_acquisitions(self.input_sequencer2)
            I2 = np.array(data["acq"]["acquisition"]["bins"]["integration"]["path0"])
            Q2 = np.array(data["acq"]["acquisition"]["bins"]["integration"]["path1"])

            amp, _, _, _ = _amp_ratio_phase_from_IQ(I + 1j * Q, I2 + 1j * Q2)

            return np.sum(amp)

        def amp_ratio_func(params, verbose):
            result = []
            for amp_ratio, phase_offset in params:
                cal_seq.mixer_corr_gain_ratio(amp_ratio)
                cal_seq.mixer_corr_phase_offset_degree(phase_offset)

                result.append(np.sum(get_data_qrm_rf()))

            if verbose:
                print(
                    f"Calibrating sideband: sideband power = {np.average(result)}",
                    end="\r",
                )
            return result

        return lambda params: amp_ratio_func(params, verbose=self.verbose)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.input_module._set_lo_enable_0(False)
        self.input_module.parent._write(
            f"SLOT{self.input_module._slot_idx}:LO:SH:ENA 1"
        )


def calibrate_lo(
    cal_module,
    cal_output,
    input_module,
    lo_freq=None,
    input_sequencer=0,
    input_sequencer2=1,
    lo_mismatch=77e6,
    verbose=False,
):
    r"""Suppress LO leakage.

    Suppress LO leakage of the mixer in `cal_module` indexed by `cal_output`
    using the QRM-RF `input_module` and return the two optimal DC offsets.

    Parameters
    ----------
    cal_module : QCM-RF or QRM-RF module
        The module that contains the mixer to calibrate. Example: cluster.module3
    cal_output : int
        The output in the module that refers to the mixer. (0 or 1)
    cal_module : QRM-RF module
        The module that is used as a measurement device. Example: cluster.module4
    lo_freq : float or None
        The LO frequency to calibrate the parameters for.
        If `None`, the LO frequency is polled from the `cal_module` and `cal_output`.
    input_sequencer : int
        One of two sequencers in the input module that should be used to calibrate.
        Note that the sequence in this sequencer will be overwritten during calibration.
    input_sequencer2 : int
        The second of two sequencers in the input module that should be used to calibrate.
        Note that the sequence in this sequencer will be overwritten during calibration.
    lo_mismatch : float
        The difference between the LO of the `input module` and mixer that is being calibrated.
    verbose : bool
        Displays the measurement results during calibration and optimal values after calibration.

    Returns
    -------
    offset_I : float
        The optimal DC offset I.
    offset_Q : float
        The optimal DC offset Q.
    """
    with _LeakageCalibrationContextManager(
        lo_freq=lo_freq,
        cal_module=cal_module,
        cal_output=cal_output,
        input_module=input_module,
        input_sequencer=input_sequencer,
        input_sequencer2=input_sequencer2,
        lo_mismatch=lo_mismatch,
        verbose=verbose,
    ) as leakage:
        cma_options = {
            "bounds": [(-84.0, -84.0), (73.0, 73.0)],
            "cma_stds": [5, 5],
            "maxfevals": 1000,
            "popsize": 20,
            "verb_disp": False,
            "ftarget": 100,
        }

        result_leakage = cma.fmin(
            None,
            parallel_objective=leakage,
            x0=[-0.1, 0.1],
            sigma0=0.2,
            options=cma_options,
        )

    cal_module.parameters[f"out{cal_output}_offset_path0"](result_leakage[0][0])
    cal_module.parameters[f"out{cal_output}_offset_path1"](result_leakage[0][1])

    return (result_leakage[0][0], result_leakage[0][1])


def calibrate_sideband(
    cal_module,
    cal_output,
    input_module,
    cal_freq=None,
    cal_sequencer=2,
    input_sequencer=0,
    input_sequencer2=1,
    lo_mismatch=77e6,
    verbose=False,
):
    r"""Suppress to suppress the undesired sideband.

    Calibrate the amplitude ratio and phase offset of the I and Q components
    in order to suppress the undesired sideband from the mixer in `cal_module`
    indexed by `cal_output` using the QRM-RF `input_module`
    and return the optimal amplitude ratio and phase offset.

    Parameters
    ----------
    cal_module : QCM-RF or QRM-RF module
        The module that contains the mixer to calibrate. Example: cluster.module3
    cal_output : int
        The output in the module that refers to the mixer. (0 or 1)
    cal_module : QRM-RF module
        The module that is used as a measurement device. Example: cluster.module4
    cal_freq : float or None
        The frequency of the desired sideband to calibrate the parameters for.
        If `None`, the frequency is polled from the `cal_module`, `cal_output` and `cal_sequencer`.
    cal_sequencer : int
        The sequencer in the output module that should be used to calibrate.
        Note that the sequence in this sequencer will be overwritten during calibration.
        The optimal parameters will also be set for this sequencer after optimization.
    input_sequencer : int
        One of two sequencers in the input module that should be used to calibrate.
        Note that the sequence in this sequencer will be overwritten during calibration.
    input_sequencer2 : int
        The second of two sequencers in the input module that should be used to calibrate.
        Note that the sequence in this sequencer will be overwritten during calibration.
    lo_mismatch : float
        The difference between the LO of the `input module` and mixer that is being calibrated.
    verbose : bool
        Displays the measurement results during calibration and optimal values after calibration.

    Returns
    -------
    amplitude ratio : float
        The optimal amplitude ratio.
    phase offset : float
        The optimal phase offset.
    """
    with _SidebandCalibrationContextManager(
        cal_freq=cal_freq,
        cal_module=cal_module,
        cal_output=cal_output,
        cal_sequencer=cal_sequencer,
        input_module=input_module,
        input_sequencer=input_sequencer,
        input_sequencer2=input_sequencer2,
        lo_mismatch=lo_mismatch,
        verbose=verbose,
    ) as sideband:
        cma_options = {
            "bounds": [(0.9, -45.0), (1.1, 45.0)],
            "cma_stds": [0.05, 5],
            "maxfevals": 1000,
            "popsize": 20,
            "verb_disp": False,
            "ftarget": 70,
        }

        result_amp_phase = cma.fmin(
            None,
            parallel_objective=sideband,
            x0=[1.0, 0.0],
            sigma0=0.2,
            options=cma_options,
        )

    cal_module[f"sequencer{cal_sequencer}"].mixer_corr_gain_ratio(
        result_amp_phase[0][0]
    )
    cal_module[f"sequencer{cal_sequencer}"].mixer_corr_phase_offset_degree(
        result_amp_phase[0][1]
    )

    return (
        result_amp_phase[0][0],
        result_amp_phase[0][1],
    )


def mixer_cal(
    cal_module,
    cal_output,
    input_module,
    cal_freq=None,
    lo_freq=None,
    cal_sequencer=2,
    input_sequencer=0,
    input_sequencer2=1,
    lo_mismatch=77e6,
    verbose=False,
):
    r"""Calibrate to suppress both the LO leakage and the undesired sideband.

    Calibrate DC offset I, DC offset Q, amplitude ratio and phase offset
    in order to suppress the LO leakage and undesired sideband from the mixer
    in `cal_module` indexed by `cal_output` using the QRM-RF `input_module`
    and return the optimal DC offset I, DC offset Q, amplitude ratio and phase offset.

    Parameters
    ----------
    cal_module : QCM-RF or QRM-RF module
        The module that contains the mixer to calibrate. Example: cluster.module3
    cal_output : int
        The output in the module that refers to the mixer. (0 or 1)
    cal_module : QRM-RF module
        The module that is used as a measurement device. Example: cluster.module4
    lo_freq : float or None
        The LO frequency of the mixer to calibrate the parameters for.
        If `None`, the LO frequency is polled from the `cal_module` and `cal_output`.
    cal_freq : float or None
        The frequency of the desired sideband to calibrate the parameters for.
        If `None`, the frequency is polled from the `cal_module`, `cal_output` and `cal_sequencer`.
    cal_sequencer : int
        The sequencer in the output module that should be used to calibrate.
        Note that the sequence in this sequencer will be overwritten during calibration.
        The optimal parameters will also be set for this sequencer after optimization.
    input_sequencer : int
        One of two sequencers in the input module that should be used to calibrate.
        Note that the sequence in this sequencer will be overwritten during calibration.
    input_sequencer2 : int
        The second of two sequencers in the input module that should be used to calibrate.
        Note that the sequence in this sequencer will be overwritten during calibration.
    lo_mismatch : float
        The difference between the LO of the `input module` and mixer that is being calibrated.
    verbose : bool
        Displays the measurement results during calibration and optimal values after calibration.

    Returns
    -------
    offset_I : float
        The optimal DC offset I.
    offset_Q : float
        The optimal DC offset Q.
    amplitude ratio : float
        The optimal amplitude ratio.
    phase offset : float
        The optimal phase offset.
    """

    offset_I, offset_Q = calibrate_lo(
        lo_freq=lo_freq,
        cal_module=cal_module,
        cal_output=cal_output,
        input_module=input_module,
        input_sequencer=input_sequencer,
        input_sequencer2=input_sequencer2,
        lo_mismatch=lo_mismatch,
        verbose=verbose,
    )

    amp_ratio, phase_offset = calibrate_sideband(
        cal_freq=cal_freq,
        cal_module=cal_module,
        cal_output=cal_output,
        cal_sequencer=cal_sequencer,
        input_module=input_module,
        input_sequencer=input_sequencer,
        input_sequencer2=input_sequencer2,
        lo_mismatch=lo_mismatch,
        verbose=verbose,
    )

    if verbose:
        print(" " * 200, end="\r")
        print(f"Best DC offsets : {result_leakage[0]}")
        print(f"Best amplitude ratio and phase offset : {result_amp_phase[0]}")

    return (
        offset_I,
        offset_Q,
        amp_ratio,
        phase_offset,
    )
