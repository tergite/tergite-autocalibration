# This code is part of Tergite
#
# (C) Copyright Liangyu Chen 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
#
# This is a modification of the following code:
# Repository: https://gitlab.com/quantify-os/quantify-scheduler
# Licensed according to the LICENCE file on the main branch
"""
A module containing factory functions for pulses on the quantum-device layer.

These factories are used to take a parametrized representation of on a operation
and use that to create an instance of the operation itself.
"""
from __future__ import annotations

from quantify_core.utilities import deprecated
from quantify_scheduler.backends.qblox.operations import (
    pulse_factories as qblox_pulse_factories,
)
from quantify_scheduler.backends.qblox.operations.stitched_pulse import StitchedPulse
from quantify_scheduler.operations import pulse_library


def composite_soft_square_pulse(  # pylint: disable=too-many-arguments
    square_amp: float,
    square_duration: float,
    square_port: str,
    square_clock: str,
    virt_z_parent_qubit_phase: float,
    virt_z_parent_qubit_clock: str,
    virt_z_child_qubit_phase: float,
    virt_z_child_qubit_clock: str,
    reference_magnitude: pulse_library.ReferenceMagnitude | None = None,
    t0: float = 0,
) -> pulse_library.SoftSquarePulse:
    """
    An example composite pulse to implement a CZ gate.

    It applies the
    square pulse and then corrects for the phase shifts on both the qubits.

    Parameters
    ----------
    square_amp
        Amplitude of the square envelope.
    square_duration
        The square pulse duration in seconds.
    square_port
        Port of the pulse, must be capable of playing a complex waveform.
    square_clock
        Clock used to modulate the pulse.
    virt_z_parent_qubit_phase
        The phase shift in degrees applied to the parent qubit.
    virt_z_parent_qubit_clock
        The clock of which to shift the phase applied to the parent qubit.
    virt_z_child_qubit_phase
        The phase shift in degrees applied to the child qubit.
    virt_z_child_qubit_clock
        The clock of which to shift the phase applied to the child qubit.
    reference_magnitude : :class:`~quantify_scheduler.operations.pulse_library.ReferenceMagnitude`, optional
        Scaling value and unit for the unitless amplitude. Uses settings in
        hardware config if not provided.
    t0
        Time in seconds when to start the pulses relative to the start time
        of the Operation in the Schedule.

    Returns
    -------
    :
        SquarePulse operation.
    """
    # composite_pulse = pulse_library.ResetClockPhase(clock=square_clock,t0=t0)

    # Start the flux pulse
    # square_amp = 0
    # composite_pulse.add_pulse(pulse_library.SoftSquarePulse(
    composite_pulse = pulse_library.SoftSquarePulse(
        amp=square_amp,
        duration=square_duration,
        port=square_port,
        clock=square_clock,
        t0=t0,
    )
    # )

    if virt_z_parent_qubit_phase is float("nan"):
        virt_z_parent_qubit_phase = 0

    if virt_z_child_qubit_phase is float("nan"):
        virt_z_child_qubit_phase = 0

    # And at the same time apply clock phase corrections
    composite_pulse.add_pulse(
        pulse_library.ShiftClockPhase(
            phase_shift=virt_z_parent_qubit_phase,
            clock=virt_z_parent_qubit_clock,
            t0=t0,
        )
    )
    composite_pulse.add_pulse(
        pulse_library.ShiftClockPhase(
            phase_shift=virt_z_child_qubit_phase,
            clock=virt_z_child_qubit_clock,
            t0=t0,
        )
    )

    return composite_pulse


@deprecated("0.20.0", qblox_pulse_factories.long_square_pulse)
def long_square_pulse() -> StitchedPulse:
    """Deprecated long_square_pulse."""


@deprecated("0.20.0", qblox_pulse_factories.staircase_pulse)
def staircase_pulse() -> StitchedPulse:
    """Deprecated staircase_pulse."""


@deprecated("0.20.0", qblox_pulse_factories.long_ramp_pulse)
def long_ramp_pulse() -> StitchedPulse:
    """Deprecated long_ramp_pulse."""
