"""
Module containing a base class that defines the basic principles used in all calibration schedule classes.
"""
import redis

redis_connection = redis.Redis(decode_responses=True)

class Measurement():

    def __init__(self,transmons: dict, couplers: dict = {}):
        self.transmons = transmons
        self.couplers = couplers
        self.qubits = list(self.transmons.keys())
        self.device_configuration = {}

    def attributes_dictionary(self, parameter):
        """
        Create a dictionary, with qubits as keys and parameters as values.
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

        if len(self.couplers) > 0:
            for coupler in self.couplers.values():
                bus = coupler.name
                for submodule in coupler.submodules.values():
                    if parameter in submodule.parameters:
                        attr_dict[bus] = submodule.parameters[parameter]()


        # print(f'{ attr_dict = }')
        return attr_dict
