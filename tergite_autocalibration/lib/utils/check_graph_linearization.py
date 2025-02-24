from typing import List

from tergite_autocalibration.lib.utils.graph import filtered_topological_order, graph as node_graph

import networkx as nx


# def get_dependencies_topological_order(G, target):
#     # Calculate the distance to the target node from all nodes it depends on
#     distance_to_target = nx.single_source_shortest_path_length(nx.reverse_view(G), target)
#
#     # Extract nodes sorted by distance
#     # Dependencies among the nodes themselves are not automatically resolved by the distance
#     sorted_nodes = list(reversed(sorted(distance_to_target, key=lambda x: distance_to_target[x])))
#
#     return sorted_nodes[:-1]  # Remove target itself


def get_dependencies_in_topological_order(graph: "nx.Graph", target, _return_list: List[str]=None) -> List[str]:
    """
    Recursively create a topological order of the node dependencies.

    Args:
        graph: Graph to iterate over.
        target: Target node to calculate the dependencies for.
        _return_list: list of nodes that are already known to be returned

    Returns:
        Nodes in topological order that target depends on.
    """

    # Initialize the return list
    if _return_list is None:
        _return_list = []

    # Find ancestor from current node
    predecessors: List[str] = list(nx.ancestors(graph, target))

    # If the node does not have any ancestors, return empty list
    if len(predecessors) == 0 or target in _return_list:
        return []

    # Otherwise iterate down through the nodes
    else:
        _new_return_list = _return_list.copy()
        # Add that node to the return
        for predecessor in predecessors:
            # This condition is to not have the same nodes twice
            if predecessor not in _new_return_list:
                _new_return_list += [predecessor]

                # Find the dependencies of this node as well and recursively go
                _new_return_list += get_dependencies_in_topological_order(graph, predecessor, _new_return_list)

        return _new_return_list


    pass




if __name__ == '__main__':
    topological_order = filtered_topological_order("ro_amplitude_two_state_optimization")
    print(topological_order)

    # Example graph
    G = nx.DiGraph()
    edges = [("A", "B"), ("B", "C"), ("D", "C"), ("C", "E"), ("E", "F")]
    G.add_edges_from(edges)

    # Get dependencies of E
    result = get_dependencies_in_topological_order(node_graph, "ro_amplitude_two_state_optimization")
    print(result)
