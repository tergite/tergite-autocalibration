# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Joel Sandås 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import matplotlib.pyplot as plt
import networkx as nx

graph = nx.DiGraph()

# dependencies: n1 -> n2. For example
# ('tof','resonator_spectroscopy')
# means 'resonator_spectroscopy' depends on 'tof'
graph_dependencies = [
    # _____________________________________
    # these are edges on  a directed graph
    # _____________________________________
    ("tof", "resonator_spectroscopy"),
    ("resonator_spectroscopy", "coupler_resonator_spectroscopy"),
    ("qubit_01_spectroscopy", "coupler_resonator_spectroscopy"),
    ("resonator_spectroscopy", "qubit_01_spectroscopy"),
    ("qubit_01_spectroscopy", "coupler_spectroscopy"),
    ("resonator_spectroscopy", "qubit_01_cw_spectroscopy"),
    ("qubit_01_spectroscopy", "rabi_oscillations"),
    ("rabi_oscillations", "ramsey_correction"),
    ("rabi_oscillations", "T1"),
    ("ramsey_correction", "motzoi_parameter"),
    ("motzoi_parameter", "n_rabi_oscillations"),
    ("n_rabi_oscillations", "resonator_spectroscopy_1"),
    ("resonator_spectroscopy_1", "ro_frequency_two_state_optimization"),
    ("ro_frequency_two_state_optimization", "ro_amplitude_two_state_optimization"),
    ("n_rabi_oscillations", "all_XY"),
    ("resonator_spectroscopy_1", "qubit_12_spectroscopy"),
    ("qubit_12_spectroscopy", "rabi_oscillations_12"),
    ("rabi_oscillations_12", "ramsey_correction_12"),
    ("ramsey_correction_12", "motzoi_parameter_12"),
    ("motzoi_parameter_12", "n_rabi_oscillations_12"),
    ("n_rabi_oscillations_12", "resonator_spectroscopy_2"),
    ("resonator_spectroscopy_2", "ro_frequency_three_state_optimization"),
    ("ro_frequency_three_state_optimization", "ro_amplitude_three_state_optimization"),
    ("T1", "T2"),
    ("T2", "T2_echo"),
    ("T2_echo", "randomized_benchmarking_ssro"),
    ("T2_echo", "purity_benchmarking"),
    ("resonator_spectroscopy_2", "cz_chevron_test"),
    ("ro_amplitude_three_state_optimization", "cz_characterisation_chevron"),
    ("cz_characterisation_chevron", "cz_chevron"),
    ("resonator_spectroscopy_2", "cz_chevron"),
    ("resonator_spectroscopy_2", "cz_parametrization_fix_duration"),
    ("resonator_spectroscopy_2", "cz_chevron_amplitude"),
    ("resonator_spectroscopy_2", "reset_chevron"),
    ("resonator_spectroscopy_2", "reset_calibration_ssro"),
    ("resonator_spectroscopy_2", "cz_calibration_ssro"),
    ("ro_amplitude_three_state_optimization", "cz_calibration_swap_ssro"),
    ("ro_amplitude_three_state_optimization", "process_tomography_ssro"),
    ("cz_calibration_ssro", "cz_dynamic_phase_ssro"),
    ("cz_dynamic_phase_ssro", "cz_dynamic_phase_swap_ssro"),
    ("resonator_spectroscopy_2", "tqg_randomized_benchmarking_ssro"),
    #    ("cz_dynamic_phase_swap_ssro", "tqg_randomized_benchmarking_ssro"),
    (
        "tqg_randomized_benchmarking_ssro",
        "tqg_randomized_benchmarking_interleaved_ssro",
    ),
]

graph.add_edges_from(graph_dependencies)
# For DEVELOPMENT PURPOSES the nodes that update an existing redis redis_field
# are given a refine attr so they can be skipped if desired
graph.add_node("tof", type="refine")
graph.add_node("punchout")
graph.add_node("resonator_relaxation")
# graph.add_node('qubit_01_spectroscopy_pulsed')
graph.add_node("qubit_01_spectroscopy")
# graph.add_node('T1', type='refine')
# graph.add_node('T2', type='refine')
# graph.add_node('T2_echo', type='refine')
# graph.add_node('ramsey_correction', type='refine')
# graph.add_node('adaptive_motzoi_parameter', type='refine')
# graph.add_node('n_rabi_oscillations', type='refine')
# graph.add_node('ramsey_correction_12', type='refine')
# graph.add_node('ro_frequency_optimization_gef', type='refine')
# graph.add_node('ro_amplitude_optimization_gef', type='refine')
# graph.add_node('resonator_spectroscopy_2', type='refine')

# for nodes that perform the same measurement,
# assign a weight to the corresponding edge to sort them
# graph['resonator_spectroscopy']['qubit_01_spectroscopy_pulsed']['weight'] = 2
# graph['resonator_spectroscopy']['qubit_01_spectroscopy']['weight'] = 1
graph["resonator_spectroscopy_1"]["qubit_12_spectroscopy"]["weight"] = 2
graph["resonator_spectroscopy_1"]["qubit_12_spectroscopy"]["weight"] = 1

initial_pos = {
    "tof": (0, 1),
    "resonator_spectroscopy": (0, 0.9),
    "qubit_01_spectroscopy": (0.0, 0.85),
    # 'qubit_01_spectroscopy_pulsed': (-0.5,0.8),
    "rabi_oscillations": (0, 0.8),
    "ramsey_correction": (0, 0.75),
    "adaptive_motzoi_parameter": (0.0, 0.7),
    "n_rabi_oscillations": (0.0, 0.65),
    "resonator_spectroscopy_1": (0, 0.6),
    "ro_frequency_two_state_optimization": (-0.2, 0.45),
    "ro_amplitude_two_state_optimization": (-0.2, 0.35),
    # 'qubit_12_spectroscopy_pulsed': (-0.5,0.4),
    "qubit_12_spectroscopy": (0.0, 0.55),
    "rabi_oscillations_12": (0, 0.5),
    "ramsey_correction_12": (0, 0.45),
    "resonator_spectroscopy_2": (0, 0.4),
    "ro_frequency_three_state_optimization": (0.15, 0.35),
    "ro_amplitude_three_state_optimization": (0.15, 0.25),
    "cz_characterisation_chevron": (0.0, 0.2),
    "cz_chevron": (0.1, 0.2),
    "cz_calibration": (-0.9, 0.0),
    "T1": (0.25, 0.55),
    "T2": (0.35, 0.55),
    "T2_echo": (0.5, 0.55),
    "randomized_benchmarking": (0.45, 0.4),
    "state_discrimination": (0.5, 0.3),
    "coupler_spectroscopy": (0.3, 0.7),
    "punchout": (0.3, 0.9),
}


# all_nodes = list(nx.topological_sort(graph))
# print(f'{ list(graph.predecessors("cz_chevron")) = }')
# graph.remove_node('coupler_spectroscopy')
# print(f'{ list(graph.predecessors("cz_chevron")) = }')


# TODO add condition argument and explanation
def filtered_topological_order(target_node: str):
    print("Targeting node: " + target_node)
    return range_topological_order("resonator_spectroscopy", target_node)


def range_topological_order(from_node: str, target_node: str):
    coupler_path = []
    if target_node == "punchout":
        topo_order = ["punchout"]

    if target_node == "resonator_relaxation":
        topo_order = ["resonator_relaxation"]
    else:
        topo_order = nx.shortest_path(graph, from_node, target_node, weight="weight")

    def graph_condition(node, types):
        is_without_type = "type" not in graph.nodes[node]
        if is_without_type:
            return True
        has_correct_type = graph.nodes[node]["type"] in types
        return not is_without_type and has_correct_type

    filtered_order = [node for node in topo_order if graph_condition(node, "refine")]
    filtered_order = coupler_path + filtered_order
    return filtered_order


if __name__ == "__main__":
    # nx.draw_spring(graph, with_labels=True, k=1, pos = initial_pos)
    # pos = nx.spring_layout(graph, k=0.3)
    nx.draw(
        graph,
        with_labels=True,
        pos=initial_pos,
        node_color="#FDFD96",
        node_shape="o",
        node_size=500,
    )
    # nx.draw(graph, pos=nx.spring_layout(graph, k=0.3), with_labels=True)
    plt.show()
