from tergite_acl.config.settings import REDIS_CONNECTION
from tergite_acl.lib.demod_channels import ParallelDemodChannels

class BaseNode:
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = node_dictionary
        self.backup = False
        self.type = 'simple_sweep' # TODO better as Enum type
        self.qubit_state = 0 # can be 0 or 1 or 2
        self.plots_per_qubit = 1 # can be 0 or 1 or 2
        self.build_demod_channels()

        self.lab_instr_coordinator = None

        self.schedule_samplespace = {}
        self.external_samplespace = {}

        self.samplespace = self.schedule_samplespace | self.external_samplespace

        # self.external_parameters = {}
        # self.node_externals = []

    # @property
    # def samplespace(self) -> dict:
    #     '''
    #     to be implemented by the child nodes
    #     '''
    #     return {}

    def pre_measurement_operation(self):
        '''
        To be implemented by the child measurement nodes
        '''
        pass

    @property
    def dimensions(self) -> list:
        '''
        array of dimensions used for raw dataset reshaping
        in utills/dataset_utils.py. some nodes have peculiar dimensions
        e.g. randomized benchmarking and need dimension definition in their class
        '''
        schedule_settable_quantities = self.schedule_samplespace.keys()

        # keeping the first element, ASSUMING that all settable elements
        # have the same dimensions on their samplespace
        first_settable = list(schedule_settable_quantities)[0]
        measured_elements = self.schedule_samplespace[first_settable].keys()
        first_element = list(measured_elements)[0]

        dimensions = []
        for quantity in schedule_settable_quantities:
            dimensions.append(
                len(self.schedule_samplespace[quantity][first_element])
            )
        return dimensions

    @property
    def external_dimensions(self) -> list:
        '''
        array of dimensions used for raw dataset reshaping
        in utills/dataset_utils.py. some nodes have peculiar dimensions
        e.g. randomized benchmarking and need dimension definition in their class
        '''
        external_settable_quantities = self.external_samplespace.keys()

        # keeping the first element, ASSUMING that all settable elements
        # have the same dimensions on their samplespace
        # i.e. all qubits have the same number of ro frequency samples in readout spectroscopy
        first_settable = list(external_settable_quantities)[0]
        measured_elements = self.external_samplespace[first_settable].keys()
        first_element = list(measured_elements)[0]

        dimensions = []
        if len(dimensions) > 1:
            raise NotImplementedError('Multidimensional External Samplespace')
        for quantity in external_settable_quantities:
            dimensions.append(
                len(self.external_samplespace[quantity][first_element])
            )
        return dimensions


    def build_demod_channels(self):
        """
        The default demodulation channels are multiplexed single-qubit channels,
        which means that you only readout one qubit in parallel.
        It works when you only calibrate single qubits.
        In many cases, you also need jointly readout multiple qubits such as quantum
        state tomography.
        Rewrite this method in these nodes.

        TODO: Add parameters to the global variables
        """
        self.demod_channels = ParallelDemodChannels.build_multiplexed_single_demod_channel(
            self.all_qubits,
            ["0", "1"],
            'IQ',
            REDIS_CONNECTION
        )

    def __str__(self):
        return f'Node representation for {self.name} on qubits {self.all_qubits}'

    def __format__(self, message):
        return f'Node representation for {self.name} on qubits {self.all_qubits}'

    def __repr__(self):
        return f'Node({self.name}, {self.all_qubits})'

