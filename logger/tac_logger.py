import logging
import logging.handlers

# setting up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
syslog = logging.StreamHandler()
formatter=logging.Formatter("%(asctime)s \u25c6 %(filename)s \u25c6 %(message)s")
syslog.setFormatter(formatter)
logger.addHandler(syslog)
# logger.propagate

