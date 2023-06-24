import numpy as np
from qcodes.instrument.parameter import ManualParameter
np.set_printoptions(precision=3, linewidth=125)

class Measurement():

    def __init__(self,transmons,connections):
        self.transmons = transmons
        self.connection_mapping = connections
        self.dimensions = {}
        self.batch_parameter_space = {}
        self.gettable_real_imag = False
        self.gettable_batched = False
        self.qubits = list(self.transmons.keys())
        self.device_configuration = {}

    def attributes_dictionary(self, parameter):
        """ Create a dictionary, with qubits as keys and parameters as values.
        The values are actual values str or float, not qcodes references.
        """
        attr_dict = {qubit: self.transmons[qubit][parameter]() for qubit in self.qubits}
        return attr_dict
