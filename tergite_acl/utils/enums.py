# This code is part of Tergite
from enum import Enum


# Used by check_data to indicate outcome
class DataStatus(Enum):
    in_spec = 1
    out_of_spec = 2
    bad_data = 3
    undefined = 4


class ClusterMode(Enum):
    """
    Used to set the cluster mode e.g. dummy cluster or real cluster
    """
    real = 0
    dummy = 1
