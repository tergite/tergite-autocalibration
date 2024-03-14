import networkx as nx
import matplotlib.pyplot as plt

graph = nx.DiGraph()

# dependencies: n1 -> n2. For example
# ('tof','resonator_spectroscopy')
# means 'resonator_spectroscopy' depends on 'tof'
graph_dependencies = [
    # _____________________________________
    # these are edges on  a directed graph
    # _____________________________________
    ('tof', 'resonator_spectroscopy'),
    # ('resonator_spectroscopy', 'coupler_resonator_spectroscopy'),
    # ('resonator_spectroscopy', 'qubit_01_spectroscopy_pulsed'),
    ('qubit_01_spectroscopy', 'coupler_spectroscopy'),
    ('resonator_spectroscopy', 'qubit_01_spectroscopy'),
    # ('qubit_01_spectroscopy_pulsed', 'rabi_oscillations'),
    ('qubit_01_spectroscopy', 'rabi_oscillations'),
    ('rabi_oscillations', 'ramsey_correction'),
    ('ramsey_correction', 'motzoi_parameter'),
    ('motzoi_parameter', 'n_rabi_oscillations'),
    ('n_rabi_oscillations', 'resonator_spectroscopy_1'),
    ('randomized_benchmarking', 'T1'),
    ('n_rabi_oscillations', 'resonator_spectroscopy_1'),
    # ('n_rabi_oscillations', 'T1'),
    ('n_rabi_oscillations', 'randomized_benchmarking'),
    ('resonator_spectroscopy_1', 'ro_frequency_two_state_optimization'),
    ('ro_frequency_two_state_optimization', 'ro_amplitude_two_state_optimization'),
    # ('randomized_benchmarking', 'T1'),
    ('T1', 'T2'),
    ('T2', 'T2_echo'),
    # ('T2_echo', 'ramsey_correction'),
    # ('resonator_spectroscopy_1', 'qubit_12_spectroscopy_pulsed'),
    ('resonator_spectroscopy_1', 'qubit_12_spectroscopy'),
    # ('qubit_12_spectroscopy_pulsed', 'rabi_oscillations_12'),
    # ('qubit_12_spectroscopy_multidim', 'cz_optimize_chevron'),
    ('qubit_12_spectroscopy', 'rabi_oscillations_12'),
    ('rabi_oscillations_12', 'ramsey_correction_12'),
    ('ramsey_correction_12', 'resonator_spectroscopy_2'),
    ('resonator_spectroscopy_2', 'ro_frequency_three_state_optimization'),
    ('ro_frequency_three_state_optimization', 'ro_amplitude_three_state_optimization'),
    # ('coupler_spectroscopy', 'cz_chevron'),
    ('ro_amplitude_three_state_optimization', 'cz_chevron'),
    # ('rabi_oscillations', 'reset_chevron'),
    # ('cz_chevron', 'cz_calibration'),
    # ('qubit_12_spectroscopy_multidim', 'cz_calibration'),
    # ('cz_calibration', 'cz_calibration_ssro'),
    # ('cz_calibration', 'cz_calibration_ssro'),
    # ('cz_calibration', 'cz_dynamic_phase')
]

graph.add_edges_from(graph_dependencies)
# For DEVELOPMENT PURPOSES the nodes that update an existing redis redis_field
# are given a refine attr so they can be skipped if desired
graph.add_node('tof', type='refine')
graph.add_node('punchout')
# graph.add_node('qubit_01_spectroscopy_pulsed')
graph.add_node('qubit_01_spectroscopy')
# graph.add_node('T1', type='refine')
# graph.add_node('T2', type='refine')
# graph.add_node('T2_echo', type='refine')
# graph.add_node('ramsey_correction', type='refine')
# graph.add_node('motzoi_parameter', type='refine')
# graph.add_node('n_rabi_oscillations', type='refine')
# graph.add_node('ramsey_correction_12', type='refine')
# graph.add_node('ro_frequency_optimization_gef', type='refine')
# graph.add_node('ro_amplitude_optimization_gef', type='refine')
# graph.add_node('resonator_spectroscopy_2', type='refine')

# for nodes that perform the same measurement,
# assign a weight to the corresponding edge to sort them
# graph['resonator_spectroscopy']['qubit_01_spectroscopy_pulsed']['weight'] = 2
# graph['resonator_spectroscopy']['qubit_01_spectroscopy']['weight'] = 1
graph['resonator_spectroscopy_1']['qubit_12_spectroscopy']['weight'] = 2
graph['resonator_spectroscopy_1']['qubit_12_spectroscopy']['weight'] = 1

initial_pos = {
    'tof': (0,1),
    'resonator_spectroscopy': (0,0.9),
    'qubit_01_spectroscopy': ( 0.0,0.85),
    # 'qubit_01_spectroscopy_pulsed': (-0.5,0.8),
    'rabi_oscillations': (0,0.8),
    'ramsey_correction': (0,0.75),
    'motzoi_parameter': (0.0,0.7),
    'n_rabi_oscillations': (0.0,0.65),
    'resonator_spectroscopy_1': (0,0.6),
    'ro_frequency_two_state_optimization': (-0.2,0.45),
    'ro_amplitude_two_state_optimization': (-0.2,0.35),
    # 'qubit_12_spectroscopy_pulsed': (-0.5,0.4),
    'qubit_12_spectroscopy': (0.0,0.55),
    'rabi_oscillations_12': (0,0.5),

    'ramsey_correction_12': (0,0.45),
    'resonator_spectroscopy_2': (0,0.4),
    'ro_frequency_three_state_optimization': (0.15,0.35),
    'ro_amplitude_three_state_optimization': (0.15,0.25),
    'cz_chevron': (0.0,0.2),
    'cz_calibration': (-0.9,0.0),
    'T1': (0.25,0.55),
    'T2': (0.35,0.55),
    'T2_echo': (0.5,0.55),
    'randomized_benchmarking': (0.45,0.4),
    'state_discrimination': (0.5,0.3),
    'coupler_spectroscopy': (0.3,0.7),
    'punchout': (0.3,0.9),
}


# all_nodes = list(nx.topological_sort(graph))
# print(f'{ list(graph.predecessors("cz_chevron")) = }')
# graph.remove_node('coupler_spectroscopy')
# print(f'{ list(graph.predecessors("cz_chevron")) = }')

# TODO add condition argument and explanation
def filtered_topological_order(target_node: str):
    target_ancestors = nx.ancestors(graph, target_node)
    if 'coupler_spectroscopy' in target_ancestors:
        coupler_path = nx.shortest_path(graph, 'resonator_spectroscopy', 'coupler_spectroscopy')
        graph.remove_node('coupler_spectroscopy')
    else:
        coupler_path = []

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

    filtered_order = [node for node in topo_order if graph_condition(node, 'refine')]
    filtered_order = coupler_path + filtered_order
    # print(f'{ filtered_order = }')
    # quit()
    return filtered_order


if __name__ == "__main__":
    # nx.draw_spring(graph, with_labels=True, k=1, pos = initial_pos)
    # pos = nx.spring_layout(graph, k=0.3)
    nx.draw(graph, with_labels=True, pos = initial_pos,node_color='#FDFD96', node_shape='o',node_size=500)
    # nx.draw(graph, pos=nx.spring_layout(graph, k=0.3), with_labels=True)
    plt.show()

