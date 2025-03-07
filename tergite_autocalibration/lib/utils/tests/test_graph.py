# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from typing import Set

import networkx as nx

from tergite_autocalibration.lib.utils.graph import (
    get_dependencies_in_topological_order,
)


def _check_no_ancestors_behind(
    graph: "nx.DiGraph", node: str, behind: Set[str]
) -> bool:
    return len(set(nx.ancestors(graph, node)).intersection(behind)) == 0


def test_dependencies_simple_graph():
    """
    Simple linear normal case
    """
    G = nx.DiGraph()
    edges = [
        ("A", "B"),
        ("B", "C"),
        ("C", "D"),
        ("D", "E"),
    ]
    G.add_edges_from(edges)

    topological_order = get_dependencies_in_topological_order(G, "D")

    assert topological_order == ["A", "B", "C"]


def test_dependencies_complex_graph():
    """
    Normal case with normal dependencies within the graph
    """
    G = nx.DiGraph()
    edges = [
        ("A", "B"),
        ("B", "C"),
        ("C", "D"),
        ("C", "E"),
        ("E", "I"),
        ("A", "F"),
        ("B", "F"),
        ("F", "G"),
        ("G", "I"),
        ("F", "H"),
        ("H", "I"),
        ("I", "J"),
    ]
    G.add_edges_from(edges)

    topological_order = get_dependencies_in_topological_order(G, "I")

    # Check whether all dependencies are in
    for node in nx.ancestors(G, "I"):
        assert node in topological_order

    # Check whether they are in correct order by checking that they are not in incorrect order
    for i in range(len(topological_order)):
        behind = topological_order[i:]
        assert _check_no_ancestors_behind(G, topological_order[i], behind)


def test_dependencies_single_node():
    """
    Edge case with just one single node in the graph
    """
    G = nx.DiGraph()
    G.add_node("X")

    topological_order = get_dependencies_in_topological_order(G, "X")

    assert topological_order == []
