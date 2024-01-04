"""
Module containing a schedule class for Ramsey calibration. (1D parameter sweep, for 2D see ramsey_detunings.py)
"""
from quantify_scheduler.enums import BinMode
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Measure, Reset, X90, Rxy, X, CZ
from quantify_scheduler.operations.pulse_library import DRAGPulse,SetClockFrequency,NumericalPulse,SoftSquarePulse,SquarePulse
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
            #TODO temporarily comment out as they are hardcoded in the schedule
            #'cz_pulse_duration': self.attributes_dictionary('cz_pulse_duration'),
            #'cz_pulse_width': self.attributes_dictionary('cz_pulse_width'),
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
            # cz_pulse_amplitudes: dict[str,np.ndarray],
            cz_pulse_durations: dict[str,np.ndarray],
            #TODO temporarily comment out as they are hardcoded in the schedule
            #cz_pulse_duration: dict[str,float],
            #cz_pulse_width: dict[str,float],
            testing_group: int = 0,
            repetitions: int = 4096,
            mock_data: bool = False,
            swap: bool = False,
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
        print('----------------')
        print("BIN_MODE:", self.bin_mode)
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
        # bus_list = [['q21','q22']]
        # this_coupler = 'q21_q22'
        print(f'{mw_frequencies = }')
        print(f'{mw_frequencies_12 = }')
        for bus_pair in bus_list:
           f11=mw_frequencies[bus_pair[0]]+mw_frequencies[bus_pair[1]]
           f20=mw_frequencies[bus_pair[0]]+mw_frequencies_12[bus_pair[0]]
           f02=mw_frequencies[bus_pair[1]]+mw_frequencies_12[bus_pair[1]]
           freq_cz[bus_pair[0]+'_'+bus_pair[1]] = np.min(np.abs(np.array([f20,f02])-f11))

        print(f'{freq_cz = }')
        cz_frequency_values = np.array(list(cz_pulse_frequencies_sweep.values())[0])
        # cz_amplitude_values = list(cz_pulse_amplitudes.values())[0]
        cz_duration_values = list(cz_pulse_durations.values())[0]

        # cz_duration, cz_width = cz_pulse_duration[qubits[0]], cz_pulse_width[qubits[0]]
        # cz_duration, cz_width = 200e-9, 4e-9

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
                ClockResource(name=this_coupler+'.cz',freq=-freq_cz[this_coupler])
            )


        #This is the common reference operation so the qubits can be operated in parallel
        #for this_coupler in self.couplers.values():
            # this_coupler.cz.square_duration(cz_duration)

        #cz_frequency_values = cz_pulse_frequencies_sweep_values[this_coupler]
        number_of_freqs = len(cz_frequency_values)

        # The intermediate loop, iterates over all cz_amplitudes
        for ampl_indx, cz_duration in enumerate(cz_duration_values):

            #The inner for loop iterates over all frequency values:
            for acq_index, cz_freq_sweep in enumerate(cz_frequency_values):
                # The outer loop, iterates over all couplers
                for this_coupler in couplers_list:
                    # this_coupler = 'q21_q22'
                    cz_clock = f'{this_coupler}.cz'
                    cz_pulse_port = f'{this_coupler}:fl'
                    set_frequency = schedule.add(
                        SetClockFrequency(clock=cz_clock, clock_freq_new=-freq_cz[this_coupler]-cz_freq_sweep),
                    )

                relaxation = schedule.add(Reset(*qubits), label=f"Reset_{acq_index}_{ampl_indx}")

                # print(cz_amplitude_index,cz_amplitude)
                if swap:
                    x = schedule.add(X('q21'), ref_op=relaxation, ref_pt='end')
                else:
                    for this_qubit in qubits:
                        x = schedule.add(X(this_qubit), ref_op=relaxation, ref_pt='end')
                for this_coupler in couplers_list:
                    # self.couplers[this_coupler].cz.square_amp(0)
                    # self.couplers[this_coupler].cz.square_duration(cz_duration)
                    # functional range 0.01 to 0.1, noticable non-linerity from 0.2 and above
                    # self.couplers[this_coupler].cz.square_amp(0.1)
                    # cz = schedule.add(CZ('q21', 'q22'), ref_op=x, ref_pt='end')
                    cz_amplitude = 0.2
                    cz = schedule.add(
                            SquarePulse(
                                duration=cz_duration,
                                amp = cz_amplitude,
                                port=cz_pulse_port,
                                clock=cz_clock,
                            ),
                            ref_op=x, ref_pt='end',
                        )

                for this_qubit in qubits:
                    #this_index = cz_index*number_of_amplitudes+cz_amplitude_index
                    this_index = ampl_indx * number_of_freqs + acq_index
                    schedule.add(Measure(this_qubit, acq_index=this_index, bin_mode=self.bin_mode),
                                    ref_op=cz,rel_time=40e-9, ref_pt="end",
                                    )
        return schedule

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
        #return schedule
