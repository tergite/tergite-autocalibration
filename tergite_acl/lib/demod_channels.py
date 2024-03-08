from itertools import product, chain
from collections import defaultdict
import numpy as np

def generate_state_labels(states_demod:list[str], joint_qubit_num:int=1):
    """
    Paras:
        states_demod:
            A list of single-qubit states like ["0","1","2",...]
            or a list of multi-qubit states like ["00", "01", "10", "11", ...].
            A mixture of them is prohibited. 
        joint_qubit_num:
            The number of qubits to be jointly readout.

    Return:
        A list of state labels.
    """
    qubit_num_input = set(len(state) for state in states_demod)
    if len(qubit_num_input) > 1:
        raise ValueError("The states used in discrimination shouldn't be a mixture of single-qubit states and multi-qubit states")  
    else:
        qubit_num_input = qubit_num_input.pop()
        if qubit_num_input == 1:
            return [f'{"".join(state)}' for state in product(*([states_demod] * joint_qubit_num))]
        else:
            if qubit_num_input != joint_qubit_num:
                raise ValueError(f"The multi-qubit states {states_demod} doesn't match the number of qubits: {joint_qubit_num}")
            else:
                return states_demod
            
def single_qubit_discrimination_states(state_labels:list[str]):
    states = [[] for _ in range(len(state_labels[0]))]
    for label in state_labels:
        for i, char in enumerate(label):
            if char not in states[i]:
                states[i].append(char)
    return states
            
class DemodChannel:
    """
    Each DemodChannel only represents one demodulation channel. 
    It could be either a single-qubit channel or a multi-qubit channel.
    """
    def __init__(self, qubits:list[str], state_labels:list[str], data_type:str, redis_connection):
        if not isinstance(qubits, (list, tuple)):
            qubits = [qubits]
        self.qubits = qubits
        self.channel_label = '_'.join(self.qubits)
        self.state_labels = state_labels
        # self.centers = defaultdict(dict)
        self.demod_info = defaultdict(dict)
        assert data_type in ["prob", "IQ"]
        self.data_type = data_type
        if data_type == "prob":
            self.qubit_states = states = single_qubit_discrimination_states(state_labels)
            for qubit, state in zip(qubits, states):
                registry = redis_connection.hgetall(f'transmons:{qubit}')
                for char in state:
                    try:
                        state_info = registry[f'some key'] # revise here
                    except KeyError:
                        raise KeyError("Please run state discrimination node in advance.")
                    else:
                        self.demod_info[qubit][char] = eval(state_info)

class ParallelDemodChannels:
    """
    Union of demod channels.
    """
    def __init__(self, channels:list[DemodChannel]):
        data_type = set(channel.data_type for channel in channels)
        assert len(data_type) == 1, "All demod channels must have the same data type."
        self.data_type = data_type.pop()
        self.demod_channels = channels
        self.qubits_demod = []
        qubits_all = chain.from_iterable([channel.qubits for channel in self.demod_channels])
        for qubit in qubits_all:
            if qubit not in self.qubits_demod:
                self.qubits_demod.append(qubit)

    @classmethod
    def build_multiplexed_single_demod_channel(cls, qubits, states_demod, data_type, redis_connection):
        channels = [DemodChannel(qubit, generate_state_labels(states_demod, 1), data_type, redis_connection) for qubit in qubits]
        return cls(channels)
    
    def set_bin_mode(self, bin_mode:str):
        assert bin_mode.upper() in ['APPEND', 'AVERAGE']
        for channel in self.demod_channels:
            channel.bin_mode = bin_mode

    def set_repetitions(self, repetitions:int):
        for channel in self.demod_channels:
            channel.repetitions = repetitions