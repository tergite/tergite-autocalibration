import numpy as np
import redis
np.set_printoptions(precision=3, linewidth=125)

redis_connection = redis.Redis(decode_responses=True)

class Measurement():

    def __init__(self,transmons):
        self.transmons = transmons
        # self.connection_mapping = connections
        # self.dimensions = {}
        # self.batch_parameter_space = {}
        # self.gettable_real_imag = False
        # self.gettable_batched = False
        self.qubits = list(self.transmons.keys())
        self.device_configuration = {}

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
