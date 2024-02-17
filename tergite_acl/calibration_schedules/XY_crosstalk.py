"""
Module containing a schedule class for XY cross-talk measurement.
"""
from quantify_scheduler.resources import ClockResource
from quantify_scheduler import Schedule
from quantify_scheduler.operations.pulse_library import DRAGPulse, SetClockFrequency
from quantify_scheduler.operations.gate_library import Measure, Reset
from tergite_acl.calibration_schedules.measurement_base import Measurement

import numpy as np

class XY_cross(Measurement):

    def __init__(self,transmons):
        super().__init__(transmons)

        self.static_kwargs = {
            'qubits': self.qubits,
            'mw_frequencies': self.attributes_dictionary('f01'),
            # 'mw_amplitudes': self.attributes_dictionary('mw_amp180'),
            'mw_pulse_ports': self.attributes_dictionary('microwave'),
            # 'mw_pulse_durations': self.attributes_dictionary('mw_pulse_duration'),
        }

    #TODO this schedule isn't complete yet, see the todo's in XY_crosstalk.py in the tergite-auto-calibration-server.
    def schedule_function(
            self,
            drive_qubit: str,
            qubits: list[str],
            mw_frequencies: dict[str,float],
            mw_amplitudes: dict[str,np.ndarray],
            mw_pulse_ports: dict[str,str],
            mw_pulse_durations: dict[str,np.ndarray],
            repetitions: int = 1024, #TODO missing the cross_case Boolean parameter (implemented in the tergite-auto-calibration-server)
        ) -> Schedule:
        """
        Generate a schedule for performing an XY cross-talk measurement which is used
        to find the qubit control line sensitivity between certain qubits.

        Schedule sequence
            Reset -> Gaussian pulse -> Measure
        This is the same sequence as for the Rabi schedule, however this time
        the Rabi experiment is performed multiple times for different pulse amplitudes.
        Note also that the input and output qubits will differ in this case.
        
        For more details on crosstalk measurments see the following article:
        P. A. Spring, S. Cao, T. Tsunoda, et al., “High coherence and low cross-talk in a tileable 3d integrated 
        superconducting circuit architecture,” Science Advances, vol. 8, no. 16, 2022.

        Parameters
        ----------
        #TODO explain parameters after the schedule has been completed.

        Returns
        -------
        :
            An experiment schedule.
        """

        schedule = Schedule("XY_cross_talk",repetitions)

        # for this_qubit, mw_f_val in mw_frequencies.items():
            # print('sorry for spamming', this_qubit)
        # schedule.add_resource(
        #     # Initialiaze the clock, at the drive port. The frequency value doesn't matter
        #     ClockResource( name=f'{drive_qubit}.01', freq=4.2e9)
        # )

        schedule.add(Reset(*qubits), label="Reset")

        #On the outer loop we loop over all qubits
        for this_qubit in qubits:
            # !!! We set the drive port clock but with the measure qubit frequency !!!:
            # schedule.add(
            #     SetClockFrequency(clock=f'{drive_qubit}.01', clock_freq_new=mw_frequencies[this_qubit])
            # )
            schedule.add_resource(
                ClockResource(name=f'{drive_qubit}.01', freq=mw_frequencies[this_qubit])
            )

            #On the middle loop we loop over all amplitudes for each qubit
            for amplitude in mw_amplitudes[this_qubit]:

                #On the inner loop we loop over the pulse durations
                for acq_index, mw_duration in enumerate(mw_pulse_durations[this_qubit]):

                    schedule.add(
                        DRAGPulse(
                            duration=mw_duration,
                            G_amp=amplitude,
                            D_amp=0,
                            port=mw_pulse_ports[drive_qubit], # This is where we change the input port
                            clock=f'{drive_qubit}.01',
                            phase=0,
                        ),
                    )

                    schedule.add( Measure(this_qubit, acq_index=acq_index), )

                    schedule.add(Reset(*qubits))

        return schedule
