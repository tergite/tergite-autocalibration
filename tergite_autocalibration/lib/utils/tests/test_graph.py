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
import pytest

from tergite_autocalibration.lib.utils.graph import (
    get_dependencies_in_topological_order,
    range_dependencies_in_topological_order,
)


def _check_no_ancestors_behind(
    graph: "nx.DiGraph", node: str, behind: Set[str]
) -> bool:
    return len(set(nx.ancestors(graph, node)).intersection(behind)) == 0


@pytest.fixture
def simple_graph() -> nx.DiGraph:
    graph = nx.DiGraph()
    edges = [
        ("A", "B"),
        ("B", "C"),
        ("C", "D"),
        ("D", "E"),
    ]
    graph.add_edges_from(edges)
    return graph


@pytest.fixture
def complex_graph() -> nx.DiGraph:
    graph = nx.DiGraph()
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
    graph.add_edges_from(edges)
    return graph


def test_dependencies_simple_graph(simple_graph):
    """
    Simple linear normal case
    """
    topological_order = get_dependencies_in_topological_order(simple_graph, "D")

    assert topological_order == ["A", "B", "C"]


def test_dependencies_complex_graph(complex_graph):
    """
    Normal case with normal dependencies within the graph
    """
    topological_order = get_dependencies_in_topological_order(complex_graph, "I")

    # Check whether all dependencies are in
    for node in nx.ancestors(complex_graph, "I"):
        assert node in topological_order

    # Check whether they are in correct order by checking that they are not in incorrect order
    for i in range(len(topological_order)):
        behind = topological_order[i:]
        assert _check_no_ancestors_behind(complex_graph, topological_order[i], behind)


def test_dependencies_single_node():
    """
    Edge case with just one single node in the graph
    """
    graph = nx.DiGraph()
    graph.add_node("X")

    topological_order = get_dependencies_in_topological_order(graph, "X")

    assert topological_order == []


def test_range_dependencies_simple_graph(simple_graph):
    """
    Normal case with simple graph
    """
    topological_order = range_dependencies_in_topological_order(
        simple_graph, ["B"], "D"
    )

    assert topological_order == ["B", "C"]


def test_range_dependencies_complex_graph(complex_graph):
    """
    Normal case with complex graph
    """
    topological_order = range_dependencies_in_topological_order(
        complex_graph, ["F"], "I"
    )

    assert len(topological_order) == 3
    assert "F" in topological_order
    assert "G" in topological_order
    assert "H" in topological_order


def test_range_dependencies_complex_graph_multi_node(complex_graph):
    """
    Normal case with complex graph with multiple nodes
    """
    topological_order = range_dependencies_in_topological_order(
        complex_graph, ["F", "C"], "I"
    )

    assert len(topological_order) == 5
    assert "F" in topological_order
    assert "G" in topological_order
    assert "H" in topological_order
    assert "C" in topological_order
    assert "E" in topological_order
