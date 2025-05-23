# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Joel Sandås 2024
# (C) Copyright Michele Faucci Giannelli 2024
# (C) Copyright Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from typing import List, Union

import networkx as nx

from tergite_autocalibration.utils.logging import logger

# IMPORTANT: If you update the node graph, please make sure to also update the documentation under
#            docs_editable/available_nodes.qmd

# These are the dependencies to construct the calibration graph from.
# The graph is a directed acyclic graph (DAG).

# Dependencies: n1 -> n2. For example:
# ('tof','resonator_spectroscopy')
# means 'resonator_spectroscopy' depends on 'tof'.
GRAPH_DEPENDENCIES = [
    ("tof", "resonator_spectroscopy"),
    ("resonator_spectroscopy", "resonator_spectroscopy_vs_current"),
    ("resonator_spectroscopy", "qubit_01_spectroscopy"),
    ("resonator_spectroscopy", "qubit_01_spectroscopy_AR"),
    ("qubit_01_spectroscopy_AR", "rabi_oscillations_AR"),
    ("resonator_spectroscopy_vs_current", "qubit_spectroscopy_vs_current"),
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
    ("punchout", "resonator_spectroscopy"),
    ("T1", "T2"),
    ("T2", "T2_echo"),
    ("ro_amplitude_three_state_optimization", "randomized_benchmarking_ssro"),
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
    (
        "tqg_randomized_benchmarking_ssro",
        "tqg_randomized_benchmarking_interleaved_ssro",
    ),
]

# Construct the calibration graph from its dependencies
CALIBRATION_GRAPH = nx.DiGraph()
CALIBRATION_GRAPH.add_edges_from(GRAPH_DEPENDENCIES)

# Add nodes that do not have any dependencies
CALIBRATION_GRAPH.add_node("tof")
CALIBRATION_GRAPH.add_node("punchout")
CALIBRATION_GRAPH.add_node("resonator_relaxation")

# These nodes will be excluded by default from the graph as their measurements are standalone
EXCLUDED_NODES = ["tof", "punchout"]


def get_dependencies_in_topological_order(
    graph: "nx.DiGraph", target_node: str, exclude_nodes: List[str] = None
):
    """
    Get dependencies of a graph in topological order.
    This implementation takes into account that there might be parallel dependencies.
    The dependency information from excluded nodes will be respected.

    Args:
        graph: Graph to get dependencies from.
        target_node: Target node to request dependencies from.
        exclude_nodes: Nodes that should be excluded from the dependency search.

    Returns:
        A list of nodes in topological order.

    """

    # Helper function to filter ancestors and exclude nodes
    if exclude_nodes is None:
        exclude_nodes = EXCLUDED_NODES

    def filter_ancestors(graph_, target_, exclude_):
        return set(nx.ancestors(graph_, target_)).difference(set(exclude_))

    # These are all nodes in the final result, but not ordered yet
    nodes_to_visit = filter_ancestors(graph, target_node, exclude_nodes)

    # We collect the dependencies for each node in the list of ancestors for the target
    ancestors = {}
    for node_to_visit in nodes_to_visit:
        ancestors[node_to_visit] = filter_ancestors(graph, node_to_visit, exclude_nodes)

    # The final result is a list in topological order that reflects dependencies
    topological_order = []
    exit_condition = len(nodes_to_visit)
    while len(nodes_to_visit) > 0:
        # We take a copy of the nodes to visit, because otherwise the loop below would throw an error
        to_visit_copy = nodes_to_visit.copy()

        # We iterate over all nodes that are not in the final result yet
        for node_to_visit in nodes_to_visit:
            # If all ancestors of the node are included in the result, we add it to the list
            # The base case and first node to be added is a node without any dependencies
            if ancestors[node_to_visit].issubset(set(topological_order)):
                # If we found a node, we add it to the result
                topological_order.append(node_to_visit)
                # And we remove it from the temporary set of nodes to visit
                to_visit_copy.remove(node_to_visit)

        # We update the nodes to visit and iterate again in the while loop until it is empty
        nodes_to_visit = to_visit_copy

        # This is to ensure that the loop is not running forever if it is impossible to find the dependencies
        exit_condition -= 1
        if exit_condition < 0:
            raise RuntimeError(
                f"Dependencies for node {target_node} in the given graph cannot be found."
                f"Please check the dependency graph."
            )

    return topological_order


def range_dependencies_in_topological_order(
    graph: "nx.DiGraph",
    from_nodes: List[str],
    target_node: str,
    exclude_nodes: List[str] = None,
):
    """
    Get a subset of the graph in topological order.

    Args:
        graph: Graph to get dependencies from.
        from_nodes: Nodes to start from.
        target_node: End range node.
        exclude_nodes: Nodes that should be excluded from the dependency search.

    Returns:
        A topologically ordered subset of the all nodes including from_nodes.

    """
    if exclude_nodes is None:
        exclude_nodes = []

    # Topological order to target_node
    topological_order = get_dependencies_in_topological_order(
        graph, target_node, exclude_nodes=exclude_nodes
    )

    # All predecessors from from_node
    back_range = set(from_nodes)
    for from_node in from_nodes:
        back_range = back_range.union(set(nx.descendants(graph, from_node)))

    # Filter the topologically sorted list by all predecessors
    return list(filter(lambda node: node in back_range, topological_order))


def filtered_topological_order(
    target_node: str, from_nodes: Union[str, List[str]] = None
):
    """
    Get the graph in topological order.

    Args:
        target_node: Target node to end at.
        from_nodes: Option to define a range in between.

    Returns:
        Topological order of nodes including target node

    """
    logger.info("Targeting node: " + target_node)

    if from_nodes is None:
        topological_order = get_dependencies_in_topological_order(
            CALIBRATION_GRAPH, target_node, exclude_nodes=EXCLUDED_NODES
        )
    else:
        topological_order = range_dependencies_in_topological_order(
            CALIBRATION_GRAPH, from_nodes, target_node, exclude_nodes=EXCLUDED_NODES
        )

    return topological_order + [target_node]
