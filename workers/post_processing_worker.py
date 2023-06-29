'''Analyze the measured dataset and extract the qoi (quantity of interest)'''

from logger.tac_logger import logger
logger.info('entering post_process module')

import xarray as xr

import redis
from rq import Queue

redis_connection = redis.Redis('localhost',6379,decode_responses=True)
# redis_connection = redis.Redis('localhost',6789,decode_responses=True)
rq_supervisor = Queue(
        'calibration_supervisor', connection=redis_connection
        )

def post_process(result_dataset: xr.Dataset):
    logger.info('Starting post process')
    pass
