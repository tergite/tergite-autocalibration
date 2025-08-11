# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2025
# (C) Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from dash import dcc, html


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
            html.H2("Select Date:"),
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
        style={"marginBottom": "20px"},
    )

    # Shows the folder of a specific calibration run
    intermediate_selection_DIV = html.Div(
        [
            html.H2("Select the calibration chain:"),
            dcc.Dropdown(
                id={"type": "intermediate-selector", "index": index},
                value=None,
                clearable=False,
            ),
        ],
        style={"marginBottom": "20px"},
    )

    # Shows the selection for the specific folder of a single measurement
    inner_selection_DIV = html.Div(
        [
            html.H2("Select a Node Measurement:"),
            dcc.Dropdown(
                id={"type": "inner-selector", "index": index},
                value=None,
                clearable=False,
            ),
        ],
        style={"marginBottom": "20px"},
    )

    # A tab view with one tab for the image and another tab for the json object with the qubit definition
    image_display_DIV = html.Div(
        [
            dcc.Tabs(
                id={"type": "tabs", "index": index},
                value="image",
                children=[
                    dcc.Tab(
                        label="Preview Image Display",
                        value="image",
                        style={"backgroundColor": "#f0f0f0"},
                    ),
                    dcc.Tab(
                        label="Device JSON Display",
                        value="json",
                        style={"backgroundColor": "#c9c9c9"},
                    ),
                ],
            ),
            html.Div(id={"type": "tab-content", "index": index}),
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
            outer_selection_DIV,
            intermediate_selection_DIV,
            inner_selection_DIV,
            image_display_DIV,
            element_selector_DIV,
            y_dim_selector_DIV,
            slice_display_DIV,
        ],
        style={
            "width": "100%" if index == "" else "45%",
            "display": "inline-block",
            "verticalAlign": "top",
            "marginLeft": "20px",
        },
    )
    return selection_layout
