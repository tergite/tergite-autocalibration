import networkx as nx
import matplotlib.pyplot as plt

graph_1 = nx.DiGraph()
# graph_1.add_edges_from([("root", "a"), ("a", "b"), ("a", "e"), ("b", "c"), ("b", "d"), ("d", "e")])

graph_dependencies = [
        ('resonator_spectroscopy','qubit_01_spectroscopy_pulsed'),
        ('resonator_spectroscopy','qubit_01_spectroscopy_multidim'),
        ('qubit_01_spectroscopy_pulsed','rabi_oscillations'),
        ('qubit_01_spectroscopy_multidim','rabi_oscillations'),
        ('rabi_oscillations','ramsey_correction'),
        ('ramsey_correction','resonator_spectroscopy_1'),
        ('resonator_spectroscopy_1','qubit_12_spectroscopy_pulsed'),
        ('qubit_12_spectroscopy_pulsed','rabi_oscillations_12'),
        ('rabi_oscillations_12','ramsey_correction_12'),
    ]


graph_1.add_edges_from(graph_dependencies)
graph_1.add_node('qubit_34', type='fast')
graph_1.add_node('qubit_01_spectroscopy_multidim', type='accurate')

nx.draw(graph_1)
# plt.show()

graph_1.nodes['qubit_01_spectroscopy_multidim']['type'] = 'accurate'
print(graph_1.nodes.data())
# print(graph_1['qubit_01_spectroscopy_multidim']['type'])
