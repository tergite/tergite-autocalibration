# Import ipython widgets
import json
import math
import os

import ipywidgets as widgets
import matplotlib.pyplot
import numpy as np
import rich
import pandas as pd

# Set up the environment.
import scipy.signal
from IPython.display import display
from ipywidgets import fixed, interact, interact_manual, interactive

from qblox_instruments import Cluster, PlugAndPlay, Pulsar
from IPython.display import display, HTML
display(HTML("<style>.container { width:100% !important; }</style>"))

#Waveform dictionary (data will hold the samples and index will be used to select the waveforms in the instrument).
waveforms = {
             "I":     {"data": [], "index": 0},
             "Q":     {"data": [], "index": 1}
            }

waveforms["I"]["data"] = [0.2]*8000
waveforms["Q"]["data"] = [0.0]*8000

#Sequence program.
prog = f"start: set_mrk 15 \n play 0,1,1000\n set_mrk 15 \n play 0,1,1000\njmp @start"

#Sequence program which stops.
# prog = """
#         move 1250000, R0
#         set_mrk    15
# start:
#         reset_ph
#         upd_param  4
#         play       0,1,4
#         wait       7996
#         loop       R0,@start
#         set_mrk    0
#         upd_param  4
#         stop
# """

#Reformat waveforms to lists if necessary.
for name in waveforms:
    if str(type(waveforms[name]["data"]).__name__) == "ndarray":
        waveforms[name]["data"] = waveforms[name]["data"].tolist()  # JSON only supports lists

#Add sequence program and waveforms to single dictionary and write to JSON file.
wave_and_prog_dict = {"waveforms": waveforms, "weights": {}, "acquisitions": {}, "program": prog}
with open("sequence.json", 'w', encoding='utf-8') as file:
    json.dump(wave_and_prog_dict, file, indent=4)
    file.close()

# close all previous connections to the cluster
Cluster.close_all()

#device_name = "pingu_cluster"
device_name = "loki_cluster"
# ip_address = connect.v./alue
ip_address = '192.0.2.72'
# connect to the cluster and reset
cluster = Cluster(device_name, ip_address)
cluster.reset()
print(f"{device_name} connected at {ip_address}")
# cluster.identify()

# Find all QRM/QCM modules
cluster.reset()

# List of all QxM modules present

module = 'module20'
print(module)
qxm = getattr(cluster, module)
print(f"{module} connected")
print(cluster.get_system_state())