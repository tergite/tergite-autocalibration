import sys
sys.path.insert(0, "../")
from workers.compilation_worker import load_redis_config, load_redis_config_coupler, \
                                        ExtendedTransmon, CompositeSquareEdge, hw_config, \
                                        QuantumDevice, SerialCompiler

def get_device(qubits):
    device = QuantumDevice(f'LokiA_bring_up_device')
    device.hardware_config(hw_config)
    transmons = {}
    for channel, q in qubits:
        transmon = ExtendedTransmon(q)
        load_redis_config(transmon,channel)
        device.add_element(transmon)
        transmons[q] = transmon
    return device