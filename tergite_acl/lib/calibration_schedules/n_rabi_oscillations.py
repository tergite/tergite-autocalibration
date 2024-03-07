"""
Module containing a schedule class for DRAG pulse motzoi parameter calibration.
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler.resources import ClockResource
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse
from quantify_scheduler.operations.gate_library import Measure, Reset
from tergite_acl.lib.measurement_base import Measurement
import numpy as np

class N_Rabi_Oscillations(Measurement):

    def __init__(self,transmons, qubit_state=0):
        super().__init__(transmons)
        self.transmons = transmons
        self.static_kwargs = {
            'qubits': self.qubits,
            'mw_frequencies': self.attributes_dictionary('f01'),
            'mw_amplitudes': self.attributes_dictionary('amp180'),
            'mw_pulse_durations': self.attributes_dictionary('duration'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
            'mw_motzois': self.attributes_dictionary('motzoi'),
        }

    def schedule_function(
            self,
            qubits: list[str],
            mw_frequencies: dict[str,float],
            mw_amplitudes: dict[str,float],
            mw_pulse_ports: dict[str,str],
            mw_pulse_durations: dict[str,float],
            mw_motzois: dict[str,float],
            mw_amplitudes_sweep: dict[str,np.ndarray],
            X_repetitions: dict[str,np.ndarray],
            repetitions: int = 1024,
        ) -> Schedule:
        """
        Generate a schedule for a DRAG pulse calibration measurement that gives the optimized motzoi parameter.
        This calibrates the drive pulse as to account for errors caused by higher order excitations of the qubits.

        Schedule sequence
            Reset -> DRAG pulse -> Inverse DRAG pulse -> Measure
        Note: Step 2 and 3 are repeated X_repetition amount of times

        For more details on the motzoi parameter and DRAG pulse calibration see the following article:
        S. Balasiu, “Single-qubit gates calibration in pycqed using superconducting qubits,” ETH, 2017.

        Parameters
        ----------
        self
            Contains all qubit states.
        qubits
            The list of qubits on which to perform the experiment.
        mw_frequencies
            Frequency of the DRAG pulse for each qubit.
        **mw_amplitudes
           2D sweeping parameter arrays.
           X_repetition: The amount of times that the DRAG pulse and inverse DRAG pulse are applied
           mw_amplitude: Amplitude of the DRAG pulse for each qubit.
        mw_pulse_ports
            Location on the device where the DRAG pulse is applied.
        mw_clocks
            Clock that the frequency of the DRAG pulse is assigned to for each qubit.
        mw_pulse_durations
            Duration of the DRAG pulse for each qubit.
        repetitions
            The amount of times the Schedule will be repeated.
        mw_motzois
            The mozoi parameter values of the DRAG (and inverse DRAG) pulses.
        

        Returns
        -------
        :
            An experiment schedule.
        """
        schedule = Schedule("mltplx_nrabi",repetitions)

        for this_qubit, mw_f_val in mw_frequencies.items():
            schedule.add_resource(
                ClockResource( name=f'{this_qubit}.01', freq=mw_f_val)
            )

        #This is the common reference operation so the qubits can be operated in parallel
        root_relaxation = schedule.add(Reset(*qubits), label="Reset")

        # The outer loop, iterates over all qubits
        for this_qubit, X_values in X_repetitions.items():
            this_clock = f'{this_qubit}.01'

            mw_amplitudes_values = mw_amplitudes_sweep[this_qubit]
            number_of_amplitudes = len(mw_amplitudes_values)

            schedule.add(
                Reset(*qubits), ref_op=root_relaxation, ref_pt_new='end'
            ) #To enforce parallelism we refer to the root relaxation

            # The intermediate loop iterates over all amplitude values:
            for x_index, this_x in enumerate(X_values):

                # The inner for loop iterates over all frequency values in the frequency batch:
                for mw_amplitude_index, mw_amplitude_sweep in enumerate(mw_amplitudes_values):
                    this_index = x_index*number_of_amplitudes + mw_amplitude_index
                    for _ in range(this_x):
                        schedule.add(
                                DRAGPulse(
                                    duration=mw_pulse_durations[this_qubit],
                                    G_amp=mw_amplitudes[this_qubit]+mw_amplitude_sweep,
                                    D_amp=mw_motzois[this_qubit],
                                    port=mw_pulse_ports[this_qubit],
                                    clock=this_clock,
                                    phase=0,
                                    ),
                                )
                    schedule.add(
                        Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                    )

                    schedule.add(Reset(this_qubit))

        return schedule
