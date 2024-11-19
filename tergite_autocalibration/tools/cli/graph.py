# This code is part of Tergite
#
# (C) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2024
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import typer

graph_cli = typer.Typer()


@graph_cli.command(
    help="Plot the calibration graph to the user specified target node in topological order."
)
def plot():
    from tergite_autocalibration.lib.utils.graph import filtered_topological_order
    from tergite_autocalibration.config.legacy import LEGACY_CONFIG
    from tergite_autocalibration.utils.logger.visuals import draw_arrow_chart

    n_qubits = len(LEGACY_CONFIG.qubits)
    topo_order = filtered_topological_order(LEGACY_CONFIG.target_node)
    draw_arrow_chart(f"Qubits: {n_qubits}", topo_order)
