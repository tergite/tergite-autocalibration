class Base_Node:
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = node_dictionary
        self.backup = False
        self.type = 'simple_sweep'
        self.qubit_state = 0 #can be 0 or 1

    @property
    def samplespace(self) -> dict:
        '''
        to be implemented by the child nodes
        '''
        return {}

    @property
    def dimensions(self):
        '''
        array of dimensions used for raw dataset reshaping
        in workers/dataset_utils.py. some nodes have peculiar dimensions
        e.g. randomized benchmarking and need dimension definition in their class
        '''
        settable_quantities = self.samplespace.keys()

        # keeping the first element, ASSUMING that all settable elements
        # have the same dimensions on their samplespace
        first_settable = list(settable_quantities)[0]
        measured_elements = self.samplespace[first_settable].keys()
        first_element = list(measured_elements)[0]

        dimensions = []
        for quantity in settable_quantities:
            dimensions.append(len(self.samplespace[quantity][first_element]))
        return dimensions

    def __str__(self):
        return f'Node representation for {self.name} on qubits {self.all_qubits}'

    def __format__(self, message):
        return f'Node representation for {self.name} on qubits {self.all_qubits}'

    def __repr__(self):
        return f'Node({self.name}, {self.all_qubits})'

