'''Retrieve the compiled schedule and run it'''

import asyncio

from quantify_scheduler.instrument_coordinator.instrument_coordinator import CompiledSchedule
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
rq_supervisor = Queue(
        'calibration_supervisor', connection=redis_connection
        )

Cluster.close_all()

#dummy = {str(mod): ClusterType.CLUSTER_QCM_RF for mod in range(1,16)}
#dummy["16"] = ClusterType.CLUSTER_QRM_RF
#dummy["17"] = ClusterType.CLUSTER_QRM_RF
#clusterA = Cluster("clusterA", dummy_cfg=dummy)
#clusterB = Cluster("clusterB", dummy_cfg=dummy)

clusterB = Cluster("clusterB", '192.0.2.141')
clusterA = Cluster("clusterA", '192.0.2.72')

loki_ic = InstrumentCoordinator('loki_ic')
loki_ic.add_component(ClusterComponent(clusterA))
loki_ic.add_component(ClusterComponent(clusterB))

def box_print(text: str):
    margin = 20
    print(u"\u2554" + u"\u2550" * (len(text)+margin) + u"\u2557")
    print(u"\u2551" + margin//2*" " + text + margin//2*" " + u"\u2551")
    print(u"\u255a" + u"\u2550" * (len(text)+margin) + u"\u255d")
    return

def configure_dataset(
        raw_ds: xarray.Dataset,
        sweep_parameters:dict,
        sweep_quantity:str
        ) -> xarray.Dataset:
    dataset = xarray.Dataset()
    keys = sorted(list(raw_ds.data_vars.keys()))
    sweep_values = list(sweep_parameters.values())
    qubits = list(sweep_parameters.keys())

    for key in keys:
        partial_ds = xarray.Dataset(coords={f'{sweep_quantity}_{qubits[key]}':(f'y{key}',sweep_values[key])})
        dataset = xarray.merge([dataset,partial_ds])
        dataset[f'y{key}'] = (f'y{key}', raw_ds[key].values[0], {'qubit': qubits[key]})

    return dataset


def measure( compiled_schedule: Schedule, sweep_parameters: dict, sweep_quantity: str) -> xarray.Dataset:
    logger.info('Starting measurement')
    box_print('Measuring')
    loki_ic.prepare(compiled_schedule)

    loki_ic.start()

    loki_ic.wait_done(timeout_sec=15)

    raw_dataset: xarray.Dataset = loki_ic.retrieve_acquisition()

    result_dataset = configure_dataset(raw_dataset, sweep_parameters, sweep_quantity)
    result_dict = result_dataset.to_dict()
    with open('example_ds.py','w') as f:
        f.write(str(result_dict))

    loki_ic.stop()
    logger.info('Finished measurement')
    print(result_dataset)

    rq_supervisor.enqueue(
            post_process,
            args=(result_dataset,'resonator_spectroscopy',),
            on_success=postprocessing_success_callback
            )

    return result_dataset


LOCALHOST = '127.0.0.1'
CALIBRATION_SUPERVISOR_PORT = 8006

async def notify_job_done(job_id: str):
    _, writer = await asyncio.open_connection(
        LOCALHOST, CALIBRATION_SUPERVISOR_PORT
    )
    message = ("job_done:" + job_id).encode()
    print(f"notify_job_done: {message=}")
    writer.write(message)
    writer.close()

def postprocessing_success_callback(_rq_job, _rq_connection, result):
    logger.info('post call back')
    # ensure that the notification is sent otherwise the main will stop it
    loop = asyncio.get_event_loop()
    loop.run_until_complete(notify_job_done('ID'))
