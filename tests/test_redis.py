from tergite_acl.lib.node_factory import NodeFactory
import quantify_scheduler.device_under_test.mock_setup as mock
import numpy as np
from tergite_acl.lib.schedules import Randomized_Benchmarking
import toml



nodes = NodeFactory()
transmon_configuration = toml.load('./config/device_config.toml')
qois = transmon_configuration['qoi']
setup = mock.set_up_mock_transmon_setup()
mock.set_standard_params_transmon(setup)


def test_redis_loading():
    all_nodes = nodes.node_implementations.keys()
    for node in all_nodes:
        assert node in qois['qubits'].keys() or node in qois['couplers'].keys()

def test_randomized_benchmarking():
    qubits = ['q1','q2']
    transmons = {qubit: setup[qubit] for qubit in qubits}
    rb = Randomized_Benchmarking(transmons)
    cliffords =  {
        qubit: np.array([2, 16, 128, 256, 0, 1]) for qubit in qubits
    }
    schedule = rb.schedule_function(
        qubits=qubits,
        seed=0,
        number_of_cliffords=cliffords
    )
    pass
