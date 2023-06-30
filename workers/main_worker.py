#!/usr/bin/env python
import redis
from rq import Worker, Queue

# Preload libraries
# import library_that_you_want_preloaded
#TODO setting decode_responses to False because of decoding error
redis_connection = redis.Redis(decode_responses=False)
queue = Queue('calibration_supervisor', connection=redis_connection)


# Provide the worker with the list of queues (str) to listen to.
worker = Worker(
        [queue],
        connection=redis_connection,
        log_job_description=False,
        )

worker.work(logging_level='WARN')
