# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from tergite_autocalibration.utils.logging.visuals import draw_arrow_chart


def test_plot_graph(caplog):
    """
    See whether it properly prints the node graph
    """
    with caplog.at_level("INFO"):
        draw_arrow_chart(
            "Nodes:",
            ["resonator_spectroscopy", "qubit_01_spectroscopy", "rabi_oscillations"],
        )

    assert len(caplog.records) == 6
    assert "Nodes:" in caplog.records[1].message
    assert "qubit_01_spectroscopy" in caplog.records[3].message


def test_plot_empty_graph(caplog):
    """
    Tests what happens if the node list is empty
    """
    with caplog.at_level("INFO"):
        draw_arrow_chart("Nodes:", [])

    assert len(caplog.records) == 3
