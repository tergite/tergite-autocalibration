'''Analyze the measured dataset and extract the qoi (quantity of interest)'''

from logger.tac_logger import logger
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

redis_connection = redis.Redis('localhost',6379,decode_responses=True)
rq_supervisor = Queue(
        'calibration_supervisor', connection=redis_connection
        )

def post_process(result_dataset: xr.Dataset):
    logger.info('Starting post process')
    for qubit in qubits:
        redis_connection.hset(f'transmons:{qubit}', 'ro_freq', 6e9)

