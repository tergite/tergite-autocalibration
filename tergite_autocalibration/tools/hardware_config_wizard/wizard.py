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

import json
import sys

from dash import ALL, MATCH, Dash, Input, Output, State, ctx, dcc, html

from tergite_autocalibration.tools.hardware_config_wizard.utils import (
    expand_range,
    split_range_input,
)
from tergite_autocalibration.tools.hardware_config_wizard.layout import (
    display_control_module_selection_div,
    display_readout_module_selection_div,
    hw_wizard_layout,
    module_types_layout,
    display_cluster_selection_dropdown,
    modules_in_each_cluster,
)

# Global in-memory stores
cluster_names = []
qubit_labels = []
module_type_checkbox = {}
qubit_to_modules_mapping = {}
microwave_clocks = []
readout_clocks = []
flux_clocks = []

app = Dash(__name__)

# app layout:
# Static Inputs:
# 1. cluster names
# 2. Qubit labels
# 3. clocks
# Dynamic Inputs:
# 4. modules that are in use: one input field per cluster
# 5. Module type (QCMRF, QRMRF,...) radioboxes
# 6. Qubit label to specific modules and outputs
# 7. Json preview

# general app structure:
# i. Collect static inputs from 1. 2. and 3. to create dynamic input 4.
# ii. Collect module numbers per cluster to create dynamic input 5.
# iii. Assign each module a type to create dynamic input 6.
# iv. Link each qubit to a particular control and readout module.

# ---------------- Layout ----------------
app.layout = hw_wizard_layout


# ---------------- Callbacks ----------------


@app.callback(
    Output("status", "children"),
    Input("session-init", "data"),
    prevent_initial_call=False,  # run once on load
)
def initialize_session(_):
    global cluster_names, qubit_labels, module_type_checkbox, qubit_to_modules_mapping
    global microwave_clocks, readout_clocks, flux_clocks
    cluster_names.clear()
    qubit_labels.clear()
    module_type_checkbox.clear()
    qubit_to_modules_mapping.clear()
    microwave_clocks.clear()
    readout_clocks.clear()
    flux_clocks.clear()

    return "Memory cleared on page load."


# Submit Static Hardware description
# i. Collect static inputs from 1. 2. and 3. to create dynamic input 4.
@app.callback(
    Output("cluster-input", "children"),
    Input("submit-btn", "n_clicks"),
    State("qubit-label-input", "value"),
    State("cluster-label-input", "value"),
    State("microwave-input", "value"),
    State("readout-input", "value"),
    State("flux-input", "value"),
    prevent_initial_call=True,
)
def update_static_inputs(
    n_clicks,
    qubit_labels_input,
    cluster_names_input,
    mw_val,
    ro_val,
    fl_val,
):
    """
    Collect user input for the static labels:
    Cluster names, qubit names and clocks
    Parse any ranges and store them in memory.
    Construct the next dynamic layout that requests the modules in use per cluster.
    """
    global qubit_labels, cluster_names, module_type_checkbox, qubit_to_modules_mapping
    global microwave_clocks, readout_clocks, flux_clocks

    # update cluster names list
    if cluster_names_input:
        cluster_names = [s.strip() for s in cluster_names_input.split(",") if s.strip()]

    # update qubit labels list and initialize the main dictionary of the app
    if qubit_labels_input:
        inputs = [s.strip() for s in qubit_labels_input.split(",") if s.strip()]

        qubit_labels = []
        for label in inputs:
            if "-" in label:
                qubit_range = expand_range(label)
                qubit_labels = qubit_labels + qubit_range
            else:
                qubit_labels.append(label)

        for q_label in qubit_labels:
            if q_label not in qubit_to_modules_mapping:
                qubit_to_modules_mapping[q_label] = {
                    "cluster": "",
                    "control": {"number": None, "out_port": ""},
                    "readout": {"number": None},
                }

    # Update clock lists
    if mw_val:
        microwave_clocks = [s.strip() for s in mw_val.split(",") if s.strip()]
    if ro_val:
        readout_clocks = [s.strip() for s in ro_val.split(",") if s.strip()]
    if fl_val:
        flux_clocks = [s.strip() for s in fl_val.split(",") if s.strip()]

    # Layout for providing the modules of each cluster
    modules_layout = modules_in_each_cluster(cluster_names)

    return modules_layout


# For each cluster, input the numbers of modules in use
# ii. Collect moule numbers per cluster to create dynamic input 5.
@app.callback(
    Output("module-types", "children"),
    Input("submit-btn-2", "n_clicks"),
    State({"type": "cluster-input", "index": ALL, "name": ALL}, "value"),
    State({"type": "cluster-input", "index": ALL, "name": ALL}, "id"),
    prevent_initial_call=True,
)
def update_module_numbers(n_clicks, module_numbers_input, module_numbers_input_ids):
    """
    Collect user input for the module numbers in use per cluster:
    Parse any ranges and store them in memory.
    Construct the next dynamic layout that defines the type of each module.
    """
    if module_numbers_input and module_numbers_input_ids:
        ziped_clusters = zip(module_numbers_input_ids, module_numbers_input)
        clusters_dict = {
            item["name"]: split_range_input(input) for item, input in ziped_clusters
        }

        number_layout = html.Div(
            [
                module_types_layout(cluster, modules)
                for cluster, modules in clusters_dict.items()
            ]
        )

        return number_layout
    return None


# Update checkbox values and highlight QRM-RF dynamically
# iii. part A. Assign each module a type to create dynamic input 6.
@app.callback(
    Output({"type": "checkbox", "index": MATCH, "cluster": MATCH}, "style"),
    Input({"type": "checkbox", "index": MATCH, "cluster": MATCH}, "value"),
    State({"type": "checkbox", "index": ALL, "name": ALL}, "id"),
    prevent_initial_call=True,
)
def update_module_type_selection(selected_choice, checkbox_id):
    """
    Populate the main app dictionary upon a radio button selection.
    Highlight QRMRF modules as feedback
    """
    num = ctx.triggered_id["index"]
    cluster = ctx.triggered_id["cluster"]
    if cluster not in module_type_checkbox:
        module_type_checkbox[cluster] = {num: selected_choice}
    else:
        module_type_checkbox[cluster].update({num: selected_choice})

    if "QRM-RF" in selected_choice:
        # return {"backgroundColor": "#d4edda", "padding": "2px", "borderRadius": "4px"}
        return {"backgroundColor": "#d4edda"}
    return {}


# iii. part B. Assign each module a type to create dynamic input 6.
@app.callback(
    Output("qubit-module-mappings", "children"),
    Input("submit-btn-3", "n_clicks"),
    prevent_initial_call=True,
)
def connect_qubits_to_modules(n_clicks):
    """
    Collect all radio button selections
    to create the dynamic inputs that will link each qubit to each module
    """
    global module_type_checkbox, cluster_names

    if len(module_type_checkbox) == 1:  # only 1 cluster let's prefill the options
        cluster = next(iter(module_type_checkbox))
        modules_dict = module_type_checkbox[cluster]
        control_modules = [
            module_number
            for module_number in modules_dict
            if modules_dict[module_number] == "QCM-RF"
        ]
        readout_modules = [
            module_number
            for module_number in modules_dict
            if modules_dict[module_number] == "QRM-RF"
        ]
        control_options = control_modules
        readout_options = readout_modules
    else:
        control_options = []
        readout_options = []

    mapping_layout = html.Div(
        [
            html.Div(
                [
                    html.Span(
                        qubit, style={"marginRight": "8px", "fontWeight": "bold"}
                    ),
                    display_cluster_selection_dropdown(qubit, cluster_names),
                    display_control_module_selection_div(qubit, control_options),
                    display_readout_module_selection_div(qubit, readout_options),
                    dcc.Store(id={"type": "qubit-hardware-mapping", "qubit": qubit}),
                ],
                style={
                    "margin": "6px 0",
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "12px",
                },
            )
            for qubit in qubit_labels
        ]
    )
    return mapping_layout


# iv. Link each qubit to a particular control and readout module.
# Part A: capture the cluster
@app.callback(
    Output({"type": "qubit-control-module-dropdown", "qubit": MATCH}, "options"),
    Output({"type": "qubit-control-module-dropdown", "qubit": MATCH}, "value"),
    Output({"type": "qubit-readout-module-dropdown", "qubit": MATCH}, "options"),
    Output({"type": "qubit-readout-module-dropdown", "qubit": MATCH}, "value"),
    Input({"type": "cluster-selection-dropdown", "qubit": MATCH}, "value"),
    Input({"type": "cluster-selection-dropdown", "qubit": MATCH}, "id"),
    prevent_initial_call=True,
)
def capture_cluster_name(selected_cluster, selected_cluster_id):
    global module_type_checkbox, qubit_to_modules_mapping
    if not selected_cluster:
        return [], None, [], None
    number_checkbox = module_type_checkbox[selected_cluster]
    control_modules_numbers = [
        n for n in number_checkbox if number_checkbox[n] != "QRM-RF"
    ]
    readout_modules_numbers = [
        n for n in number_checkbox if number_checkbox[n] == "QRM-RF"
    ]

    # FIXME: qubit_to_modules_mapping is updated implicitly
    qubit = selected_cluster_id["qubit"]
    qubit_to_modules_mapping[qubit]["cluster"] = selected_cluster

    return control_modules_numbers, None, readout_modules_numbers, None


# Link each qubit to the corresponding cluster-control module & out - readout module
# like every callback the order of Inputs has to be the same as the order of the
# function arguments
@app.callback(
    Output({"type": "qubit-hardware-mapping", "qubit": MATCH}, "data"),
    Input({"type": "qubit-control-module-dropdown", "qubit": MATCH}, "value"),
    Input({"type": "module-out", "qubit": MATCH}, "value"),
    Input({"type": "qubit-readout-module-dropdown", "qubit": MATCH}, "value"),
    prevent_initial_call=True,
)
def update_string_mapping(selected_num, selected_out_port, selected_readout_num):
    string_id = ctx.triggered_id["qubit"]
    if selected_num is not None:
        qubit_to_modules_mapping[string_id]["control"]["number"] = selected_num
    if selected_out_port is not None:
        qubit_to_modules_mapping[string_id]["control"]["out_port"] = selected_out_port
    if selected_readout_num is not None:
        qubit_to_modules_mapping[string_id]["readout"]["number"] = selected_readout_num

    return qubit_to_modules_mapping


# Generate JSON preview
@app.callback(
    Output("json-preview", "children"),
    Input("preview-btn", "n_clicks"),
    prevent_initial_call=True,
)
def generate_preview(n_clicks):
    MW_port_clocks = lambda q: [f"{q}:mw-{q}.{clock}" for clock in microwave_clocks]
    RO_port_clocks = lambda q: [f"{q}:res-{q}.{clock}" for clock in readout_clocks]
    FL_port_clocks = lambda q: [f"{q}:fl-{q}.{clock}" for clock in flux_clocks]

    mw_lo_configs = {
        port_clock: {"lo_freq": 4e9}
        for q in qubit_labels
        for port_clock in MW_port_clocks(q)
    }
    ro_lo_configs = {
        port_clock: {"lo_freq": 6e9}
        for q in qubit_labels
        for port_clock in RO_port_clocks(q)
    }

    mw_mixer = {
        port_clock: {
            "dc_offset_i": 0,
            "dc_offset_q": 0,
            "amp_ratio": 1,
            "phase_error": 0,
        }
        for q in qubit_labels
        for port_clock in MW_port_clocks(q)
    }

    ro_mixer = {
        port_clock: {
            "dc_offset_i": 0,
            "dc_offset_q": 0,
            "amp_ratio": 1,
            "phase_error": 0,
        }
        for q in qubit_labels
        for port_clock in RO_port_clocks(q)
    }

    def control_output_and_port(qubit_label):
        cluster_name = qubit_to_modules_mapping[qubit_label]["cluster"]
        module_number = qubit_to_modules_mapping[qubit_label]["control"]["number"]
        out = qubit_to_modules_mapping[qubit_label]["control"]["out_port"]
        output_string = f"complex_output_{out[-1]}"
        port_type = "mw"
        return [
            f"{cluster_name}.module{module_number}.{output_string}",
            f"{qubit_label}:{port_type}",
        ]

    def readout_output_and_port(qubit_label):
        cluster_name = qubit_to_modules_mapping[qubit_label]["cluster"]
        module_number = qubit_to_modules_mapping[qubit_label]["readout"]["number"]
        output_string = "complex_output_0"
        port_type = "res"
        return [
            f"{cluster_name}.module{module_number}.{output_string}",
            f"{qubit_label}:{port_type}",
        ]

    def hardware_description(cluster: str):
        modules = module_type_checkbox[cluster]
        return {
            "instrument_type": "Cluster",
            "ref": "external",
            "modules": {
                number: {"instrument_type": module_type.replace("-", "_")}
                for number, module_type in modules.items()
            },
        }

    json_data = {
        "config_type": "quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig",
        "hardware_description": {
            cluster: hardware_description(cluster) for cluster in cluster_names
        },
        "hardware_options": {
            "modulation_frequencies": {**mw_lo_configs, **ro_lo_configs},
            "mixer_corrections": {**mw_mixer, **ro_mixer},
        },
        "connectivity": {
            "graph": [control_output_and_port(q) for q in qubit_labels]
            + [readout_output_and_port(q) for q in qubit_labels]
        },
    }
    return json.dumps(json_data, indent=2)


# ---------------- Main ----------------
if __name__ == "__main__":
    port = 8050
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    app.run(debug=True, port=port)
