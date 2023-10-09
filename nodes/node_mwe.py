import networkx as nx
import matplotlib.pyplot as plt

graph_1 = nx.DiGraph()

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
graph_1.add_node('qubit_01_spectroscopy_pulsed', type='fast')
graph_1.add_node('qubit_01_spectroscopy_multidim', type='accurate')
graph_1.add_node('ramsey_correction', type='refine')
graph_1.add_node('ramsey_correction_12', type='refine')
topo_order = list(nx.topological_sort(graph_1))

def graph_condition(node, types):
    is_without_type = 'type' not in graph_1.nodes[node]
    if is_without_type: 
        return True
    has_correct_type = graph_1.nodes[node]['type'] in types
    return not is_without_type and has_correct_type

filtered_order = [node for node in topo_order if graph_condition(node,['fast','refine'])]

nx.draw(graph_1)
breakpoint()
# plt.show()

# graph_1.nodes['qubit_01_spectroscopy_multidim']['type'] = 'accurate'
# print(graph_1.nodes.data())
# print(graph_1['qubit_01_spectroscopy_multidim']['type'])
