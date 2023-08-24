'''Analyze the measured dataset and extract the qoi (quantity of interest)'''
import matplotlib.pyplot as plt
from logger.tac_logger import logger
from analysis.tac_quantify_analysis import Multiplexed_Analysis
import xarray as xr

import redis

redis_connection = redis.Redis(decode_responses=True)

def post_process(result_dataset: xr.Dataset, node: str):
    analysis = Multiplexed_Analysis(result_dataset, node)

    #figure_manager = plt.get_current_fig_manager()
    #figure_manager.window.showMaximized()

    fig = plt.gcf()
    fig.set_tight_layout(True)
    plt.show()
    analysis.node_result.update({'measurement_dataset':result_dataset.to_dict()})
