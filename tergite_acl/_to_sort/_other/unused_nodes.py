class State_Discrimination_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['discriminator']
        self.measurement_obj = Single_Shots_RO
        self.analysis_obj = StateDiscriminationAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'qubit_states': {
                qubit: np.array(110 * [0, 0, 0, 0, 1, 1, 1, 1]) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace
