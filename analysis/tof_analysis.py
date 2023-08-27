import json

import matplotlib.pyplot as plt
import numpy as np

    
# Analysis
def analyze_tof(p0,p1):
    # Determine when the signal crosses half-max for the first time (in ns)
    t_halfmax = np.where(np.abs(p0) > np.max(p0) / 2)[0][0]

    # The time it takes for a sine wave to reach its half-max value is (in ns)
    correction = 1 / 50e6 * 1e9 / 12
    # correction = 1 / readout_module.sequencer0.nco_freq() * 1e9 / 12

    #extracts TOF value
    tof_measured = t_halfmax - correction

    #makes sure that the time of flight is set to a multiple of 4 ns
    tof=tof_measured- (tof_measured % 4) + 4
    #     return tof*1e-9

    #plotting
    # if plotting:
    #     r = readout_module.get_acquisitions(0)["single"]["acquisition"]["scope"]
    #     plt.plot(r["path0"]["data"], ".-")
    #     plt.plot(r["path1"]["data"], ".-")
    #     plt.axvline(tof_measured, c="k")
    #     plt.xlim(
    #         tof_measured - 20 / readout_module.sequencer0.nco_freq() * 1e9,
    #         tof_measured + 70 / readout_module.sequencer0.nco_freq() * 1e9,
    #     )
    #     plt.ylabel('Amplitude (V)')
    #     plt.xlabel('Time (ns)')
    #     plt.show()
    #
    #     plt.plot(r["path0"]["data"], ".-")
    #     plt.plot(r["path1"]["data"], ".-")
    #     plt.axvline(1024 + tof_measured, c="k")
    #     plt.xlim(
    #         1024 + tof_measured - 10 / readout_module.sequencer0.nco_freq() * 1e9,
    #         1024 + tof_measured + 40 / readout_module.sequencer0.nco_freq() * 1e9,
    #     )
    #     plt.ylabel('Amplitude (V)')
    #     plt.xlabel('Time (ns)')
    #     plt.show()
    #
    #
    #
    #     #print('Time of flight = ', tof, ' ns')
    #     return tof*1e-9
