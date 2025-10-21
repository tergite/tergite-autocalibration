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

# General app layout
# Static Inputs:
# 1. cluster names
# 2. Qubit labels
# 3. clocks


# Dynamic Inputs:
# 4. modules that are in use: one input field per cluster
# 5. Module type (QCMRF, QRMRF,...) radioboxes
# 6. Qubit label to specific modules and outputs
# 7. Json preview

initialization = html.Div(
    [
        dcc.Store(id="session-init", data={}),
        html.H2("Hardware Configuration Wizard"),
        html.Div(id="status"),
    ]
)

# 1. cluster names
cluster_names_input_header = html.H5(
    "Provide the names of your clusters",
    style={
        "marginTop": "0px",
        "marginBottom": "0px",
    },
)
cluster_names_input_field = dcc.Input(
    id="cluster-label-input",
    type="text",
    placeholder="Enter comma-separated strings. (e.g. cluster1,cluster2,...)",
    style={
        "width": "50%",
        "marginRight": "10px",
    },
)
cluster_label_input = html.Div([cluster_names_input_header, cluster_names_input_field])


# 2. Qubit labels
qubit_label_input_header = html.H5(
    "Provide your Qubit Labels",
    style={
        "marginTop": "0px",
        "marginBottom": "0px",
    },
)
qubit_label_input_field = dcc.Input(
    id="qubit-label-input",
    type="text",
    placeholder="Enter comma-separated strings or ranges. (e.g. q01,q02,q03, q04-q12...)",
    style={
        "width": "50%",
        "marginRight": "10px",
    },
)
qubit_label_input = html.Div([qubit_label_input_header, qubit_label_input_field])


# 3. clocks
clocks_input_header = html.H5(
    "Which clocks are used in each port?",
    style={
        "marginTop": "0px",
        "marginBottom": "0px",
    },
)
clocks_input_fields = html.Div(
    [
        dcc.Input(
            id="microwave-input",
            type="text",
            placeholder="Microwave Control. e.g. 01,12",
            style={"width": "20%", "marginRight": "10px"},
        ),
        dcc.Input(
            id="readout-input",
            type="text",
            placeholder="Readout. e.g. ro,ro1,ro2 ...",
            style={"width": "20%", "marginRight": "10px"},
        ),
        dcc.Input(
            id="flux-input",
            type="text",
            placeholder="Flux. e.g. cz",
            style={"width": "20%"},
        ),
    ],
    style={"display": "flex", "gap": "10px", "marginBottom": "20px"},
)
clock_labels_input = html.Div(
    [
        clocks_input_header,
        clocks_input_fields,
        html.Button("Submit your input values", id="submit-btn", n_clicks=0),
    ]
)


# 4. modules that are in use: one input field per cluster
module_numbers_input = [
    html.H5(
        "Which modules are in use on each cluster?",
        style={
            "marginTop": "0px",
            "marginBottom": "0px",
        },
    ),
    # just a place-holder Div, the contains are generated dynamically
    # in the callback
    html.Div(id="cluster-input"),
    html.Button("Submit your input values", id="submit-btn-2", n_clicks=0),
]


# 4. modules that are in use: one input field per cluster
def modules_in_each_cluster(cluster_names: list[str]):
    cluster_modules_layout = html.Div(
        [
            html.Div(
                [
                    html.Span(
                        cluster_name, style={"marginRight": "6px", "fontWeight": "bold"}
                    ),
                    dcc.Input(
                        id={
                            "type": "cluster-input",
                            "index": num,
                            "name": cluster_name,
                        },
                        type="text",
                        placeholder="Provide the numbers of Cluster Modules in use. (e.g. 1,2,3 or 1-5,10...)",
                        style={
                            "width": "50%",
                            "marginRight": "10px",
                        },
                    ),
                ]
            )
            for num, cluster_name in enumerate(cluster_names)
        ]
    )
    return cluster_modules_layout


# 5. Module type (QCMRF, QRMRF,...) radioboxes
module_types_input = [
    html.H5(
        "What is the type of each module?",
        style={
            # "marginTop": "0px",
            "marginBottom": "0px",
        },
    ),
    # just a place-holder Div, the contains are generated dynamically
    # in the callback
    html.Div(id="module-types"),
    html.Button("Submit your input values", id="submit-btn-3", n_clicks=0),
]


# 5. Module type (QCMRF, QRMRF,...) radioboxes
def module_type_layout(cluster: str, number: int):
    module_number = html.Span(
        str(number), style={"marginRight": "6px", "fontWeight": "bold"}
    )
    types_radios = dcc.RadioItems(
        id={"type": "checkbox", "index": number, "cluster": cluster},
        options=[
            {"label": opt, "value": opt} for opt in ["QCM-RF", "QRM-RF", "QCM", "QRM"]
        ],
        # value=checkbox_store.get(num, []),
        inline=True,
        style={
            "display": "inline-flex",
            # "gap": "4px",
            # "fontSize": "12px",  # smaller text
            "margin": "0",
        },
    )
    layout = html.Div(
        [module_number, types_radios],
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "6px",
            "padding": "2px 6px",
            "border": "1px solid #ddd",
            "borderRadius": "4px",
        },
    )
    return layout


# 5. Module type (QCMRF, QRMRF,...) radioboxes
def module_types_layout(cluster: str, module_numbers: list[int]):
    specific_cluster_header = html.H5(
        cluster,
        style={
            "marginTop": "0px",
            "marginBottom": "0px",
        },
    )
    radio_display = html.Div(
        [module_type_layout(cluster, num) for num in module_numbers],
        style={"display": "flex", "flexWrap": "wrap", "gap": "6px"},
    )
    number_layout = html.Div(
        [
            specific_cluster_header,
            radio_display,
            html.Br(),
        ]
    )
    return number_layout


# 6. Qubit label to specific modules and outputs
def display_cluster_selection_dropdown(qubit: str, cluster_names: list[str]):
    if len(cluster_names) == 1:
        [cluster_name_value] = cluster_names
    else:
        cluster_name_value = None
    dropdown = dcc.Dropdown(
        id={"type": "cluster-selection-dropdown", "qubit": qubit},
        options=[{"label": cluster, "value": cluster} for cluster in cluster_names],
        value=cluster_name_value,
        placeholder="Cluster",
        style={"width": "100px", "marginRight": "0px"},
    )
    return dropdown


# 6. Qubit label to specific modules and outputs
out_ports_input = [
    html.H5(
        "Which module and which output controls and measures each qubit?",
        style={
            # "marginTop": "0px",
            "marginBottom": "0px",
        },
    ),
    # just a place-holder Div, the contains are generated dynamically
    # in the callback
    html.Div(id="qubit-module-mappings"),
]


# 6. Qubit label to specific modules and outputs
def display_control_module_selection_div(qubit: str, control_options: list[int] | None):
    control_selection = dcc.Dropdown(
        id={
            "type": "qubit-control-module-dropdown",
            "qubit": qubit,
        },
        options=control_options,
        # value:qubit_to_modules_mapping[q]["control"]["number"],
        placeholder="Control",
        style={"width": "100px", "marginRight": "0px"},
    )
    output_radios = dcc.RadioItems(
        id={"type": "module-out", "qubit": qubit},
        options=[
            {"label": "OUT0", "value": "OUT0"},
            {"label": "OUT1", "value": "OUT1"},
        ],
        # value=qubit_to_modules_mapping[q]["control"][
        #     "out_port"
        # ]:
        inline=True,
        style={
            "marginLeft": "0px",
            "marginRight": "10px",
        },
    )
    control_module_and_out = html.Div(
        [control_selection, output_radios],
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "12px",
            "border": "1px solid #ccc",
            "borderRadius": "6px",
            "padding": "6px 10px",
            "backgroundColor": "#f9f9f9",
        },
    )
    return control_module_and_out


# 6. Qubit label to specific modules and outputs
def display_readout_module_selection_div(qubit: str, readout_options: list[int] | None):
    readout_module = dcc.Dropdown(
        id={"type": "qubit-readout-module-dropdown", "qubit": qubit},
        options=readout_options,
        # value=qubit_to_modules_mapping[q]["readout"]["number"],
        placeholder="ReadOut",
        style={"width": "100px", "marginRight": "0px"},
    )
    return readout_module


# 7. Json preview
json_preview_fild = [
    html.Button(
        "Generate Preview",
        id="preview-btn",
        n_clicks=0,
        style={"marginLeft": "10px"},
    ),
    html.H4("Preview JSON configuration:"),
    html.Pre(id="json-preview", style={"border": "1px solid #ccc", "padding": "10px"}),
]

hw_wizard_layout = html.Div(
    [
        initialization,
        cluster_label_input,
        html.Br(),
        qubit_label_input,
        html.Br(),
        clock_labels_input,
        html.Br(),
        module_numbers_input[0],
        module_numbers_input[1],
        module_numbers_input[2],
        html.Br(),
        html.Br(),
        module_types_input[0],
        module_types_input[1],
        module_types_input[2],
        html.Br(),
        html.Br(),
        out_ports_input[0],
        out_ports_input[1],
        html.Br(),
        html.Br(),
        json_preview_fild[0],
        json_preview_fild[1],
        json_preview_fild[2],
    ]
)
