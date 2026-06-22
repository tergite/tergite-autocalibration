# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2025, 2026
# (C) Chalmers Next Labs 2025, 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import sys

import dash
import dash_bootstrap_components as dbc
from dash import clientside_callback, html, Output, Input

# SLATE is the prettiest but not light mode
app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.SIMPLEX])

app.title = "Data Browser - Tergite Autocalibration"

color_mode_switch = html.Span(
    [
        dbc.Label(className="fa fa-moon", html_for="color-mode-switch"),
        dbc.Switch(
            id="color-mode-switch",
            value=False,
            className="d-inline-block ms-1",
            persistence=True,
        ),
        dbc.Label(className="fa fa-sun", html_for="color-mode-switch"),
    ]
)


header = dbc.Navbar(
    dbc.Container(
        [
            # dbc.NavbarBrand("My App"),
            dbc.Nav(
                [
                    dbc.NavLink(page["name"], href=page["path"])
                    for page in dash.page_registry.values()
                ],
                navbar=True,
            ),
            dbc.Switch(
                id="color-mode-switch",
                value=True,
                persistence=True,
                className="ms-auto",
            ),
        ]
    )
)


app.layout = dbc.Container(
    [header, html.Br(), dash.page_container],
    fluid=True,
    className="bg-body text-body min-vh-100",
)

clientside_callback(
    """
    (switchOn) => {
       document.documentElement.setAttribute('data-bs-theme', switchOn ? 'light' : 'dark');  
       return window.dash_clientside.no_update
    }
    """,
    Output("color-mode-switch", "id"),
    Input("color-mode-switch", "value"),
)

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8050
    app.run(debug=True, port=port)
