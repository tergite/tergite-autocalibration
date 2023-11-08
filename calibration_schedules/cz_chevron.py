"""
Module containing a schedule class for Ramsey calibration. (1D parameter sweep, for 2D see ramsey_detunings.py)
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X, CZ
from quantify_scheduler.operations.pulse_library import DRAGPulse,SetClockFrequency,NumericalPulse,SoftSquarePulse
from quantify_scheduler.resources import ClockResource
from calibration_schedules.measurement_base import Measurement
from utilities.extended_transmon_element import Measure_RO1
from utilities.QPU_connections_visualization import edge_group
from scipy.signal import gaussian
from scipy import signal
from matplotlib import pyplot as plt

import numpy as np

class CZ_chevron(Measurement):

    def __init__(self,transmons,couplers,qubit_state:int=0):
        super().__init__(transmons)
        self.qubit_state = qubit_state
        self.couplers = couplers
        self.static_kwargs = {
            'qubits': self.qubits,
            'mw_frequencies': self.attributes_dictionary('f01'),
            'mw_pulse_durations': self.attributes_dictionary('duration'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
            'mw_ef_amps180': self.attributes_dictionary('ef_amp180'),
            'mw_frequencies_12': self.attributes_dictionary('f12'),
            'cz_pulse_duration': self.attributes_dictionary('cz_pulse_duration'),
            'cz_pulse_width': self.attributes_dictionary('cz_pulse_width'),
        }

    def schedule_function(
            self,
            qubits: list[str],
            mw_ef_amps180: dict[str,float],
            mw_frequencies: dict[str,float],
            mw_frequencies_12: dict[str,float],
            mw_pulse_ports: dict[str,str],
            mw_pulse_durations: dict[str,float],
            cz_pulse_frequencies_sweep: dict[str,np.ndarray],
            cz_pulse_amplitudes: dict[str,np.ndarray],
            cz_pulse_duration: dict[str,float],
            cz_pulse_width: dict[str,float], 
            testing_group: int = 1,
            repetitions: int = 1024,
            mock_data: bool = True,
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
        schedule = Schedule("CZ_chevron",repetitions)
        
        couplers_list_all = edge_group.keys()
        couplers_list,bus_list = [],[]
        for coupler in couplers_list_all:
            control,target = coupler.split('_')[0], coupler.split('_')[1]
            if testing_group != 0:
                check = edge_group[coupler] == testing_group
            else:
                check = True
            if control in qubits and target in qubits and check:
                bus_list.append([control,target])
                couplers_list.append(coupler)
        control, target = np.transpose(bus_list)

        freq_cz = {}
        for bus_pair in bus_list:
            f11=mw_frequencies[bus_pair[0]]+mw_frequencies[bus_pair[1]]
            f20=mw_frequencies_12[bus_pair[0]]+mw_frequencies_12[bus_pair[0]]
            f02=mw_frequencies_12[bus_pair[1]]+mw_frequencies_12[bus_pair[1]]
            freq_cz[bus_pair[0]+'_'+bus_pair[1]] = np.min(np.abs(np.array([f20,f02])-f11))

        cz_pulse_frequencies_sweep_values = cz_pulse_frequencies_sweep[qubits[0]]
        cz_amplitudes_values = cz_pulse_amplitudes[qubits[0]]
        number_of_amplitudes = len(cz_amplitudes_values)
        # cz_duration, cz_width = cz_pulse_duration[qubits[0]], cz_pulse_width[qubits[0]]
        cz_duration, cz_width = 200e-9, 4e-9

        # Add the clocks to the schedule
        for this_qubit, mw_f_val in mw_frequencies.items():
            schedule.add_resource(
                ClockResource( name=f'{this_qubit}.01', freq=mw_f_val)
            )
        for this_qubit, mw_f_val in mw_frequencies_12.items():
            schedule.add_resource(
                ClockResource(name=f'{this_qubit}.12', freq=mw_f_val)
            )
        for this_coupler in couplers_list:
            schedule.add_resource(
                ClockResource(name=f'{this_coupler}.cz', freq=
                              freq_cz[this_coupler]+cz_pulse_frequencies_sweep[qubits[0]][0]+4.4e9)
            )

        #This is the common reference operation so the qubits can be operated in parallel

        for this_coupler in self.couplers.values():
            this_coupler.cz.square_duration(cz_duration)

        for cz_index, cz_frequency_sweep in enumerate(cz_pulse_frequencies_sweep_values):
            # print(cz_index,cz_frequency_sweep)
            for this_coupler in couplers_list:
                cz_clock = f'{this_coupler}.cz'
                cz_pulse_ports = f'{this_coupler}:fl'
                set_frequency = schedule.add(
                        SetClockFrequency(clock=cz_clock, clock_freq_new=freq_cz[this_coupler]+cz_frequency_sweep+4.4e9),
                        label=f"set_freq_{this_coupler}_{cz_index}"
                    )
            for cz_amplitude_index, cz_amplitude in enumerate(cz_amplitudes_values): 
                relaxation = schedule.add(Reset(*qubits), label=f"Reset_{cz_index}_{cz_amplitude_index}")
                # print(cz_amplitude_index,cz_amplitude)
                for this_qubit in qubits:
                    x = schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                    if mock_data:
                        # print(this_qubit)
                        this_clock = f'{this_qubit}.01'

                        set_frequency_qubit = schedule.add(
                            SetClockFrequency(clock=this_clock, clock_freq_new=cz_frequency_sweep+mw_frequencies[this_qubit]),
                            label=f"set_freq_{this_qubit}_{cz_index}_{cz_amplitude_index}"
                        )
                        cz = schedule.add(DRAGPulse(
                            duration=20e-9,
                            G_amp=cz_amplitude,
                            D_amp=0,
                            port=mw_pulse_ports[this_qubit],
                            clock=this_clock,
                            phase=0,
                        ),ref_op=set_frequency_qubit,ref_pt="end")
                    if mock_data:
                        pass
                    else:
                        for this_bus in bus_list:
                            self.couplers[this_bus[0]+'_'+this_bus[1]].cz.square_amp(cz_amplitude)
                            cz = schedule.add(CZ(this_bus[0],this_bus[1])
                                    ,ref_op=x,ref_pt="end")
                        
                for this_qubit in qubits:
                    this_index = cz_index*number_of_amplitudes+cz_amplitude_index
                    schedule.add(Measure(this_qubit, acq_index=this_index, bin_mode=BinMode.AVERAGE),
                                    ref_op=cz, ref_pt="end",)
                #     # schedule.add(Reset(this_qubit))
        # Add calibration points
        # relaxation_calib = schedule.add(Reset(*qubits), label=f"Reset_Calib")
        # for this_qubit in qubits:
        #     i = this_index
        #     schedule.add(Reset(this_qubit))
        #     schedule.add(
        #         Measure(
        #             this_qubit,
        #             acq_index=i+1
        #         ),
        #         label=f"Calibration point |0> {this_qubit}",ref_op=relaxation_calib,ref_pt='end',
        #     )

        #     schedule.add(Reset(this_qubit))
        #     schedule.add(X(this_qubit))
        #     schedule.add(
        #         Measure(
        #             this_qubit,
        #             acq_index=i+2
        #         ),
        #         label=f"Calibration point |1> {this_qubit}",
        #     )
        #     f12_clock = f'{this_qubit}.12'
        #     schedule.add(Reset(this_qubit))
        #     schedule.add(X(this_qubit))
        #     f12_amp = mw_ef_amps180[this_qubit]
        #     schedule.add(
        #         DRAGPulse(
        #             duration=mw_pulse_durations[this_qubit],
        #             G_amp=f12_amp,
        #             D_amp=0,
        #             port=mw_pulse_ports[this_qubit],
        #             clock=f12_clock,
        #             phase=0,
        #         ),
        #     )
        #     schedule.add(
        #         Measure(
        #             this_qubit,
        #             acq_index=i+3
        #         ),
        #         label=f"Calibration point |2> {this_qubit}",
        #     )
        return schedule