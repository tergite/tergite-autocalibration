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
from quantify_scheduler.resources import ClockResource
import numpy as np
import math

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

    # Start the flux pulse
    composite_pulse = pulse_library.SoftSquarePulse(
        amp=square_amp,
        reference_magnitude=reference_magnitude,
        duration=square_duration,
        port=square_port,
        clock=square_clock,
        t0=t0,
    )

    print(virt_z_parent_qubit_phase, virt_z_child_qubit_phase)

    if virt_z_parent_qubit_phase is float('nan'):
        virt_z_parent_qubit_phase = 0

    if virt_z_child_qubit_phase is float('nan'):
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

    # composite_pulse = pulse_library.SoftSquarePulse(
    #     amp=0,
    #     reference_magnitude=reference_magnitude,
    #     duration=4e-9,
    #     port=square_port,
    #     clock=square_clock,
    #     t0=np.ceil( square_duration * 1e9 / 4) * 4e-9,
    # )

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
