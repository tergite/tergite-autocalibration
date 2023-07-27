import json
import math

import matplotlib.pyplot as plt
import numpy as np

from qcodes import Instrument
from qblox_instruments import Cluster

def Time_Of_Flight(cluster, plotting):

    readout_module = cluster.module16

    readout_module.out0_att(0)
    readout_module.in0_att(0)
    readout_module.out0_in0_lo_en(True)
    readout_module.out0_in0_lo_freq(6620000000)

    # From Mixer Calibration
    readout_module.out0_offset_path0(-0.0088298*1000)
    readout_module.out0_offset_path1( 0.0012304*1000)
    
    
    readout_module.sequencer0.sync_en(True)



    readout_module.arm_sequencer(0)
    readout_module.start_sequencer(0)

    for sequencer in readout_module.sequencers:
        for out in range(0, 2):
            sequencer.set("channel_map_path{}_out{}_en".format(out % 2, out), False)
    readout_module.sequencer0.channel_map_path0_out0_en(True)
    readout_module.sequencer0.channel_map_path1_out1_en(True)
    
    wfs = {
        "zero": {"index": 0, "data": [0.0] * 1024},
        "one": {"index": 1, "data": [1.0] * 1024},
    }

    acquisitions = {
        "single": {"num_bins": 1, "index": 0},
    }
    
    qrm_prog = f"""
    set_mrk   15 # switch marker
    play    1, 0, 4     # start readout pulse
    set_mrk  3 # switch marker
    acquire 0, 0, 16384 # start the 'single' acquisition sequence and wait for the length of the scope acquisition window
    stop
    """

    sequence = {
        "waveforms": wfs,
        "weights": {},
        "acquisitions": acquisitions,
        "program": qrm_prog,
    }

    with open("sequence.json", "w", encoding="utf-8") as file:
        json.dump(sequence, file, indent=4)
        file.close()
    # Upload sequence.
    readout_module.sequencer0.sequence("sequence.json")

    readout_module.sequencer0.nco_freq(50e6)
    readout_module.sequencer0.mod_en_awg(True)
    readout_module.sequencer0.demod_en_acq(True)
    readout_module.sequencer0.sync_en(True)

    readout_module.arm_sequencer(0)
    readout_module.start_sequencer(0)

    # Wait for the sequencer and acquisition to finish with a timeout period of one minute.
    readout_module.get_acquisition_state(0, 1)
    readout_module.store_scope_acquisition(0, "single")
    # Print status of sequencer.
    #print(readout_module.get_sequencer_state(0))
    
    #Analysis
    p0 = np.array(
    readout_module.get_acquisitions(0)["single"]["acquisition"]["scope"]["path0"]["data"]
    )
    p1 = np.array(
        readout_module.get_acquisitions(0)["single"]["acquisition"]["scope"]["path1"]["data"]
    )
    # Determine when the signal crosses half-max for the first time (in ns)
    t_halfmax = np.where(np.abs(p0) > np.max(p0) / 2)[0][0]

    # The time it takes for a sine wave to reach its half-max value is (in ns)
    correction = 1 / readout_module.sequencer0.nco_freq() * 1e9 / 12
    
    #extracts TOF value
    tof_measured = t_halfmax - correction
    
    #makes sure that the time of flight is set to a multiple of 4 ns
    tof=tof_measured- (tof_measured % 4) + 4
    
    #plotting
    if plotting:
        r = readout_module.get_acquisitions(0)["single"]["acquisition"]["scope"]
        plt.plot(r["path0"]["data"], ".-")
        plt.plot(r["path1"]["data"], ".-")
        plt.axvline(tof_measured, c="k")
        plt.xlim(
            tof_measured - 20 / readout_module.sequencer0.nco_freq() * 1e9,
            tof_measured + 70 / readout_module.sequencer0.nco_freq() * 1e9,
        )
        plt.ylabel('Amplitude (V)')
        plt.xlabel('Time (ns)')
        plt.show()

        plt.plot(r["path0"]["data"], ".-")
        plt.plot(r["path1"]["data"], ".-")
        plt.axvline(1024 + tof_measured, c="k")
        plt.xlim(
            1024 + tof_measured - 10 / readout_module.sequencer0.nco_freq() * 1e9,
            1024 + tof_measured + 40 / readout_module.sequencer0.nco_freq() * 1e9,
        )
        plt.ylabel('Amplitude (V)')
        plt.xlabel('Time (ns)')
        plt.show()
        
        
    
    print('Time of flight = ', tof, ' ns')
    return tof*1e-9

