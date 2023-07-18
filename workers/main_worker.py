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
