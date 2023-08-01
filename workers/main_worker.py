#!/usr/bin/env python
import redis
from rq import Worker, Queue
from rq.command import send_shutdown_command

# Preload libraries
# import library_that_you_want_preloaded
# setting decode_responses to False because of decoding error
redis_connection = redis.Redis(decode_responses=False)
redis_connection.flushdb()
queue = Queue('calibration_supervisor', connection=redis_connection)

# Resets the clusters:
from datetime import datetime
from qblox_instruments import Cluster
from qcodes.instrument.base import Instrument
import threading

def preset_cluster(name, IP):
    cluster = Cluster(name,IP)
    cluster.reset()
    pass

t0 = datetime.now()
print('Reseting Clusters')
thread_1 = threading.Thread(target=preset_cluster, args=('ClusterA', '192.0.2.72'))
thread_1.start()
thread_2 = threading.Thread(target=preset_cluster, args=('ClusterB', '192.0.2.141'))
thread_2.start()
thread_1.join()
thread_2.join()
t1 = datetime.now()
print(f'Reseting time: { t1-t0 = }')
Instrument.close_all()

# Start fresh:
queue.empty()
workers = Worker.all(redis_connection)
for w in workers:
    send_shutdown_command(redis_connection, w.name)

# Provide the worker with the list of queues (str) to listen to.
worker = Worker(
        [queue],
        connection=redis_connection,
        log_job_description=False,
        )

worker.work(logging_level='WARN')
