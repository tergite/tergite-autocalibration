# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import matplotlib.pyplot as plt
import numpy as np


# Analysis
def analyze_tof(ds, plotting):
    # Determine when the signal crosses half-max for the first time (in ns)
    p0 = ds["p0"]
    p1 = ds["p1"]
    t_halfmax = np.where(np.abs(p0) > np.max(p0) / 2)[0][0]

    # The time it takes for a sine wave to reach its half-max value is (in ns)
    correction = 1 / 50e6 * 1e9 / 12
    # correction = 1 / readout_module.sequencer0.nco_freq() * 1e9 / 12

    # extracts TOF value
    tof_measured = t_halfmax - correction

    # makes sure that the time of flight is set to a multiple of 4 ns
    tof = tof_measured - (tof_measured % 4) + 4
    print(tof * 1e-9)

    # plotting
    if plotting:
        # r = readout_module.get_acquisitions(0)["single"]["acquisition"]["scope"]
        # plt.plot(r["path0"]["data"], ".-")
        # plt.plot(r["path1"]["data"], ".-")
        plt.plot(p0, ".-")
        plt.plot(p1, ".-")
        plt.axvline(tof_measured, c="k")
        plt.xlim(
            tof_measured - 20 / 50e6 * 1e9,
            # tof_measured - 20 / readout_module.sequencer0.nco_freq() * 1e9,
            tof_measured + 70 / 50e6 * 1e9,
            # tof_measured + 70 / readout_module.sequencer0.nco_freq() * 1e9,
        )
        plt.ylabel("Amplitude (V)")
        plt.xlabel("Time (ns)")
        plt.show()

        # plt.plot(r["path0"]["data"], ".-")
        # plt.plot(r["path1"]["data"], ".-")
        # plt.axvline(1024 + tof_measured, c="k")
        # plt.xlim(
        #    1024 + tof_measured - 10 / readout_module.sequencer0.nco_freq() * 1e9,
        #    1024 + tof_measured + 40 / readout_module.sequencer0.nco_freq() * 1e9,
        # )
        # plt.ylabel('Amplitude (V)')
        # plt.xlabel('Time (ns)')
        # plt.show()

        # print('Time of flight = ', tof, ' ns')
        return tof * 1e-9
