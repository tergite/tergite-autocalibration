# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2026
# (C) Chalmers Next Labs 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import dash
from dash import html

dash.register_page(__name__, title="Documentation")

layout = html.Div(
    [
        html.H1("Link to Documentation"),
        html.A(
            html.H1("Tergite Automatic Calibration"),
            href="https://tergite.github.io/tergite-autocalibration/",
        ),
    ]
)
