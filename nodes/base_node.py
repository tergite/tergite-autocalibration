class Base_Node:
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = node_dictionary
        self.backup = True
        self.type = 'simple_sweep'

    def __str__(self):
        return f'Node representation for {self.name} on qubits {self.all_qubits}'

    def __format__(self, message):
        return f'Node representation for {self.name} on qubits {self.all_qubits}'

    def __repr__(self):
        return f'Node({self.name}, {self.all_qubits})'

