'''Analyze the measured dataset and extract the qoi (quantity of interest)'''

import matplotlib.pyplot as plt
from logger.tac_logger import logger
from analysis.tac_quantify_analysis import (
        Multiplexed_Analysis
        # Multiplexed_Resonator_Spectroscopy_Analysis,
        # Multiplexed_Two_Tones_Spectroscopy_Analysis,
        # Multiplexed_Rabi_Analysis,
        # Multiplexed_Ramsey_Analysis,
        # Multiplexed_T1_Analysis,
        # Multiplexed_Punchout_Analysis,
        # Multiplexed_Motzoi_Analysis,
        )
import xarray as xr

import redis

# ANALYSIS_MAP = {
#         'resonator_spectroscopy': Multiplexed_Resonator_Spectroscopy_Analysis,
#         'qubit_01_spectroscopy_pulsed': Multiplexed_Two_Tones_Spectroscopy_Analysis,
#         'rabi_oscillations': Multiplexed_Rabi_Analysis,
#         'T1': Multiplexed_T1_Analysis,
#         'punchout': Multiplexed_Punchout_Analysis,
#         'ramsey_correction': Multiplexed_Ramsey_Analysis,
#         'motzoi_parameter': Multiplexed_Motzoi_Analysis,
#         }

redis_connection = redis.Redis(decode_responses=True)

def post_process(result_dataset: xr.Dataset, node: str):
    # analysis_class = ANALYSIS_MAP[node]
    # analysis = analysis_class(result_dataset, node)
    analysis = Multiplexed_Analysis(result_dataset, node)

    #figure_manager = plt.get_current_fig_manager()
    #figure_manager.window.showMaximized()

    fig = plt.gcf()
    fig.set_tight_layout(True)
    plt.show()
    analysis.node_result.update({'measurement_dataset':result_dataset.to_dict()})
