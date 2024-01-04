"""
Module containing a base class that defines the basic principles used in all calibration schedule classes.
"""
import numpy as np
import redis
from quantify_scheduler.enums import BinMode

np.set_printoptions(precision=3, linewidth=125)

redis_connection = redis.Redis(decode_responses=True)

class Measurement():

    def __init__(self,transmons):
        self.transmons = transmons
        # self.connection_mapping = connections
        self.qubits = list(self.transmons.keys())
        self.device_configuration = {}
        self.bin_mode = BinMode.AVERAGE

    def attributes_dictionary(self, parameter):
        """ Create a dictionary, with qubits as keys and parameters as values.
        The values are actual values str or float, not qcodes references.
        """
        attr_dict = {}
        # breakpoint()
        for transmon in self.transmons.values():
            qubit = transmon.name
            if parameter=='readout_port':
               attr_dict[qubit] = transmon.ports.readout()
            elif parameter=='artificial_detuning':
               redis_key = f'transmons:{qubit}'
               attr_dict[qubit] = float(redis_connection.hget(f"{redis_key}",parameter))
            else:
               for submodule in transmon.submodules.values():
                   if parameter in submodule.parameters:
                       attr_dict[qubit] = submodule.parameters[parameter]()

        # print(f'{ attr_dict = }')
        return attr_dict
    
    def set_bin_mode(self, bin_mode:str):
        bin_mode = getattr(BinMode, bin_mode, None)
        if bin_mode is not None:
            self.bin_mode = bin_mode
        else:
            raise ValueError(f"bin mode {bin_mode} isn't defined in Quantify now.")
