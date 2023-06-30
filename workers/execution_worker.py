'''Retrieve the compiled schedule and run it'''

from logger.tac_logger import logger
logger.info('entering execution module')

from qblox_instruments import Cluster, ClusterType
from quantify_scheduler import Schedule
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent
import xarray
from workers.post_processing_worker import post_process

import redis
from rq import Queue

redis_connection = redis.Redis(decode_responses=True)
# redis_connection = redis.Redis('localhost',6379,decode_responses=True)
rq_supervisor = Queue(
        'calibration_supervisor', connection=redis_connection
        )

Cluster.close_all()

dummy = {str(mod): ClusterType.CLUSTER_QCM_RF for mod in range(1,16)}
dummy["16"] = ClusterType.CLUSTER_QRM_RF
dummy["17"] = ClusterType.CLUSTER_QRM_RF
clusterA = Cluster("clusterA", dummy_cfg=dummy)
clusterB = Cluster("clusterB", dummy_cfg=dummy)

loki_ic = InstrumentCoordinator('loki_ic')
loki_ic.add_component(ClusterComponent(clusterA))
loki_ic.add_component(ClusterComponent(clusterB))

def measure(compiled_schedule: Schedule) -> xarray.Dataset:
    logger.info('Starting measurement')
    loki_ic.prepare(compiled_schedule)

    loki_ic.start()

    loki_ic.wait_done(timeout_sec=15)

    result_dataset = loki_ic.retrieve_acquisition()

    loki_ic.stop()

    rq_supervisor.enqueue(post_process, args=(result_dataset,))

    return result_dataset
