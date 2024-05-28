# This code is part of Tergite
from enum import Enum

# Used by check_data to indicate outcome
class DataStatus(Enum):
    in_spec = 1
    out_of_spec = 2
    bad_data = 3
    undefined = 4

# Used to distinguish running on dummy or real clusters
class MeasurementMode(Enum):
    dummy = 1
    real = 2
