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

from dash import dcc, html
import dash_bootstrap_components as dbc


def generate_selection_layout(folder_structure: dict, index: str = ""):
    """
    Generates the folder structure to select a qubit measurement

    Args:
        folder_structure: dictionary passing the folder structure
        index: Variable to toggle between left and right view in the comparison

    Returns:

    """

    # Shows to select the folder of the measurement with the date
    outer_selection_DIV = html.Div(
        [
            html.H2("Date:"),
            dcc.Dropdown(
                id={"type": "outer-selector", "index": index},
                options=[
                    {"label": folder, "value": folder}
                    for folder in folder_structure.keys()
                ],
                value=None,
                clearable=False,
            ),
        ],
        style={"marginBottom": "20px", "width": "15%"},
    )

    # Shows the folder of a specific calibration run
    intermediate_selection_DIV = html.Div(
        [
            html.H2("Calibration chain:"),
            dcc.Dropdown(
                id={"type": "intermediate-selector", "index": index},
                value=None,
                clearable=False,
            ),
        ],
        style={"marginBottom": "20px", "width": "39%"},
    )

    # Shows the selection for the specific folder of a single measurement
    inner_selection_DIV = html.Div(
        [
            html.H2("Node Measurement:"),
            dcc.Dropdown(
                id={"type": "inner-selector", "index": index},
                value=None,
                clearable=False,
            ),
        ],
        style={"marginBottom": "20px", "width": "39%"},
    )

    selectors_DIV = html.Div(
        [
            outer_selection_DIV,
            intermediate_selection_DIV,
            inner_selection_DIV,
            dbc.Button(
                "\u2605",
                id={"type": "star-btn", "index": index},
                style={
                    "backgroundColor": "#F5F5F5",
                    "color": "#FFD700",  # star color (gold)
                    "marginBottom": "20px",
                    "width": "5%",
                    "fontSize": "2em",
                    "padding": "0.4em",
                    "borderRadius": "8px",
                },
            ),
        ],
        style={"display": "flex", "gap": "10px"},
    )

    # A tab view with one tab for the image and another tab for the json object with the qubit definition
    image_display_DIV = html.Div(
        [
            dbc.Tabs(
                id={"type": "tabs", "index": index},
                active_tab="image",
                children=[
                    dbc.Tab(
                        label="Preview Image Display",
                        tab_id="image",
                        # style={"backgroundColor": "#f0f0f0"},
                    ),
                    dbc.Tab(
                        label="Device JSON Display",
                        tab_id="json",
                        # style={"backgroundColor": "#c9c9c9"},
                    ),
                ],
            ),
            html.Div(id={"type": "tab-content", "index": index}),
        ],
        style={"marginTop": "20px"},
    )

    qoi_display_DIV = html.Div(
        [
            html.H3("Quantities of Interest"),
            html.Div(
                id={"type": "qoi-content", "index": index},
                style={
                    "display": "flex",
                    "flexWrap": "wrap",  # wrap when many keys
                    "gap": "20px",
                },
            ),
        ],
        style={"marginTop": "20px"},
    )

    element_selector_DIV = html.Div(
        [
            html.H2("Select Elements:"),
            dcc.Dropdown(
                id={"type": "element-selector", "index": index},
                multi=True,
                clearable=False,
            ),
        ],
        style={"marginTop": "20px"},
    )

    y_dim_selector_DIV = html.Div(
        [
            html.H2("Y Dimension Selector:"),
            dcc.Dropdown(id={"type": "y-dim-selector", "index": index}, multi=False),
        ],
        style={"marginTop": "20px"},
    )
    slice_display_DIV = html.Div(
        [
            html.H2("Dynamic Plot Display"),
            html.Div(
                id={"type": "dataset-container", "index": index},
                style={"display": "flex", "gap": "20px", "flexWrap": "wrap"},
            ),
        ],
        style={"marginTop": "20px"},
    )

    # Wrap up the whole page
    selection_layout = html.Div(
        [
            dcc.Store(id={"type": "full-dataset", "index": index}),
            html.H4("Starred Items", id={"index": index}),
            html.Div(id={"type": "starred-list", "index": index}),
            selectors_DIV,
            image_display_DIV,
            qoi_display_DIV,
            element_selector_DIV,
            y_dim_selector_DIV,
            slice_display_DIV,
            dcc.Store(
                id={"type": "starred-store", "index": index},
                data=[],
                storage_type="local",
            ),
        ],
        style={
            "width": "100%" if index == "" else "45%",
            "display": "inline-block",
            "verticalAlign": "top",
            "marginLeft": "20px",
        },
    )
    return selection_layout
