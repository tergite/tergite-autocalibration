'''Analyze the measured dataset and extract the qoi (quantity of interest)'''

import matplotlib.pyplot as plt
from logger.tac_logger import logger
from analysis.tac_quantify_analysis import Multiplexed_Resonator_Spectroscopy_Analysis
logger.info('entering post_process module')
#TODO this is temporary
qubits = ['q12', 'q14', 'q16', 'q17', 'q18', 'q19', 'q20',
          'q21', 'q22', 'q23', 'q24', 'q25' ]

import xarray as xr

import asyncio
from pathlib import Path
import xarray as xr


import redis
from rq import Queue

ANALYSIS_MAP = {
        'resonator_spectroscopy': Multiplexed_Resonator_Spectroscopy_Analysis
        }

redis_connection = redis.Redis(decode_responses=True)
rq_supervisor = Queue(
        'calibration_supervisor', connection=redis_connection
        )

def post_process(result_dataset: xr.Dataset, node: str):
    logger.info('Starting post process')
    analysis_class = ANALYSIS_MAP[node]
    analysis = analysis_class(result_dataset, node)

    fig = plt.gcf()
    fig.set_tight_layout(True)
    plt.show()
    analysis.node_result.update({'measurement_dataset':result_dataset.to_dict()})
