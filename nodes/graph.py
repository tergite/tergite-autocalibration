import networkx as nx

graph = nx.DiGraph()

# dependencies: n1 -> n2. For example
# ('tof','resonator_spectroscopy')
# means 'resonator_spectroscopy' depends on 'tof'
graph_dependencies = [
    ('tof', 'resonator_spectroscopy'),
    ('resonator_spectroscopy', 'coupler_spectroscopy'),
    ('resonator_spectroscopy', 'coupler_resonator_spectroscopy'),
    ('resonator_spectroscopy', 'qubit_01_spectroscopy_pulsed'),
    ('resonator_spectroscopy', 'qubit_01_spectroscopy_multidim'),
    ('qubit_01_spectroscopy_pulsed', 'rabi_oscillations'),
    ('qubit_01_spectroscopy_multidim', 'rabi_oscillations'),
    ('rabi_oscillations', 'ramsey_correction'),
    ('ramsey_correction', 'resonator_spectroscopy_1'),
    ('ramsey_correction', 'ro_frequency_optimization'),
    ('ro_frequency_optimization', 'ro_amplitude_optimization'),
    ('ro_amplitude_optimization', 'state_discrimination'),
    ('ramsey_correction', 'T1'),
    ('resonator_spectroscopy_1', 'qubit_12_spectroscopy_pulsed'),
    ('qubit_12_spectroscopy_pulsed', 'rabi_oscillations_12'),
    ('rabi_oscillations_12', 'ramsey_correction_12'),
    ('ramsey_correction_12', 'ro_frequency_optimization_gef'),
]

graph.add_edges_from(graph_dependencies)
# For DEVELOPMENT PURPOSES the nodes that update an existing redis redis_field
# are given a refine attr so they can be skipped if desired
graph.add_node('tof', type='refine')
graph.add_node('punchout')
graph.add_node('qubit_01_spectroscopy_pulsed')
graph.add_node('qubit_01_spectroscopy_multidim')
graph.add_node('ramsey_correction', type='refine')
graph.add_node('ramsey_correction_12', type='refine')
graph.add_node('ro_frequency_optimization', type='refine')
graph.add_node('ro_amplitude_optimization', type='refine')

# for nodes that perform the same measurement, 
# assign a weight to the corresponding edge to sort them
graph['resonator_spectroscopy']['qubit_01_spectroscopy_pulsed']['weight'] = 1
graph['resonator_spectroscopy']['qubit_01_spectroscopy_multidim']['weight'] = 2

all_nodes = list(nx.topological_sort(graph))

# TODO add condition argument and explanation
def filtered_topological_order(target_node: str):
    if target_node == 'new_node':
        topo_order = ['new_node']
    if target_node == 'punchout':
        topo_order = ['punchout']
    else:
        topo_order = nx.shortest_path(
            graph, 'resonator_spectroscopy', target_node, weight='weight'
        )

    def graph_condition(node, types):
        is_without_type = 'type' not in graph.nodes[node]
        if is_without_type:
            return True
        has_correct_type = graph.nodes[node]['type'] in types
        return not is_without_type and has_correct_type

    filtered_order = [node for node in topo_order if graph_condition(node, 'none')]
    return filtered_order
