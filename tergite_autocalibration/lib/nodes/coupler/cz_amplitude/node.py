from ....utils.node_subclasses import ParametrizedSweepNode

class CZ_Amplitude_Node(ParametrizedSweepNode):
    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
