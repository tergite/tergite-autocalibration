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

import base64
import json
import os
import re
import sys

import dash
import plotly.express as px
import xarray as xr
from dash import ctx, dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import MATCH, Input, Output, State, ALL
from dash_renderjson import DashRenderjson

from tergite_autocalibration.config.globals import DATA_DIR
from tergite_autocalibration.tools.browser.layout import generate_selection_layout
from tergite_autocalibration.tools.browser.utils import scan_folders

folder_structure = scan_folders(DATA_DIR)

app = dash.Dash(__name__)

app.title = "Data Browser - Tergite Autocalibration"

app.layout = html.Div(
    [
        dcc.Store(id="folder-data", data=folder_structure),
        dcc.Store(id="selected-2d-variable"),
        dcc.Store(id="starred-store", data=[], storage_type="local"),
        html.Button(
            "Refresh Folder Structure",
            id="refresh-button",
            n_clicks=0,
            style={
                "padding": "10px 20px",  # bigger button
                "marginRight": "15px",  # spacing to the right
                "fontSize": "18px",  # bigger text
                "cursor": "pointer",
            },
        ),
        html.Button(
            "Compare",
            id="compare-button",
            n_clicks=0,
            style={
                "padding": "10px 20px",
                "marginRight": "15px",
                "fontSize": "18px",
                "cursor": "pointer",
            },
        ),
        dcc.Input(
            id="text-input",
            type="text",
            debounce=True,  # triggers callback only on blur or Enter
            placeholder="Enter string for filtering",
            style={
                "padding": "10px",
                "marginRight": "15px",
                "fontSize": "18px",
                "width": "250px",
            },
        ),
        dbc.Tooltip(
            "For example if the node rabi_12_oscillations is looked for, strings like rabi_12 or 12_osc suffice.",
            target="text-input",
            placement='right',
        ),
        html.Div(
            id="filter-confirmation", style={"marginTop": "10px", "color": "green"}
        ),
        html.Div(id="selection-panel"),
    ]
)


@app.callback(
    Output("selection-panel", "children"), Input("compare-button", "n_clicks")
)
def toggle_compare(n_clicks: int):
    """
    Callback for the toggle button in the top row

    Args:
        n_clicks: Number of clicks, used to identify whether to toggle view

    Returns:

    """

    if n_clicks % 2 == 1:
        return html.Div(
            [
                generate_selection_layout(folder_structure, index="A"),
                generate_selection_layout(folder_structure, index="B"),
            ]
        )
    return generate_selection_layout(folder_structure)


@app.callback(
    Output({"type": "outer-selector", "index": MATCH}, "options"),
    Input("folder-data", "data"),
)
def update_outer_folders( folder_data: dict):
    """
    Callback to update the outer folders in the first dropdown menu
    with the selection for the dates.
    It is used particularly when a filter string is applied, to filter out
    date folders that dont contain measurements containing the filter string.

    Args:
        folder_data: What is inside that folder

    Returns:

    """
    if folder_data:
        return [{"label": f, "value": f} for f in folder_data.keys()]
    return []

@app.callback(
    Output({"type": "intermediate-selector", "index": MATCH}, "options"),
    Input({"type": "outer-selector", "index": MATCH}, "value"),
    Input("folder-data", "data"),
)
def update_intermediate_folders(selected_outer: str, folder_data: dict):
    """
    Callback to update the intermediate folders in the second dropdown menu
    with the selection for the calibration runs.

    Args:
        selected_outer: Outer folder with the date
        folder_data: What is inside that folder

    Returns:

    """
    if selected_outer and selected_outer in folder_data:
        return [{"label": f, "value": f} for f in folder_data[selected_outer].keys()]
    return []


@app.callback(
    Output({"type": "inner-selector", "index": MATCH}, "options"),
    Input({"type": "intermediate-selector", "index": MATCH}, "value"),
    Input({"type": "outer-selector", "index": MATCH}, "value"),
    Input("folder-data", "data"),
)
def update_inner_folders(
    selected_intermediate: str, selected_outer: str, folder_data: dict
):
    """
    Callback to update the inner folders with the selection for the measurements

    Args:
        selected_intermediate: Selected folder for the calibration run
        selected_outer: Selected outer folder with the calibration date
        folder_data: What is inside that calibration run folder

    Returns:

    """

    if (
        selected_outer
        and selected_intermediate
        and selected_outer in folder_data
        and selected_intermediate in folder_data[selected_outer]
    ):
        return [
            {"label": f, "value": f}
            for f in folder_data[selected_outer][selected_intermediate]
        ]
    return []


# -----------------------
# Callback: Star selected items
# -----------------------
@app.callback(
    Output({"type": "starred-store", "index": MATCH}, "data"),
    Input({"type": "star-btn", "index": MATCH}, "n_clicks"),
    State({"type": "outer-selector", "index": MATCH}, "value"),
    State({"type": "intermediate-selector", "index": MATCH}, "value"),
    State({"type": "inner-selector", "index": MATCH}, "value"),
    State({"type": "starred-store", "index": MATCH}, "data"),
    prevent_initial_call=True,
)
def star_selected(n_clicks, outer_selected, interm_selected, inner_selected, starred):

    if not (outer_selected and interm_selected and inner_selected):
        return starred

    selected = os.path.join(outer_selected, interm_selected, inner_selected)
    starred = starred or []
    if selected not in starred:
        starred.append(selected)
    else:
        starred.remove(selected)
    return starred


@app.callback(
    Output("folder-data", "data"),
    Output("filter-confirmation", "children"),
    Input("refresh-button", "n_clicks"),
    Input("text-input", "value"),
    prevent_initial_call=True,
)
def refresh_folder_structure(n_clicks: int, filter_text: str):
    """
    Callback to refresh the outer folder structure

    Args:
        n_clicks: Unused
        filter_text: User provided string.
                     Only measurement folders containing this string are regarded valid.

    Returns:

    """
    triggered_id = ctx.triggered_id

    # If triggered by folder refresh and no input filter is active
    if triggered_id == "refresh-button" and not filter_text:
        return scan_folders(DATA_DIR), ""

    # If triggered by text input and input is not empty
    if triggered_id == "text-input":
        # Case 1: Empty text -> reload original structure
        if not filter_text.strip():
            return scan_folders(DATA_DIR), "Filter cleared. Showing all folders"

        # Case 2: Text input filters the intermediate folders
        styled_text_span = html.Span(
            filter_text, style={"color": "blue", "fontWeight": "bold"}
        )
        confirmation_message = html.Div(
            ["Filter applied: ", styled_text_span],
            style={"marginTop": "10px"},
        )
        return (scan_folders(DATA_DIR, filter_text=filter_text), confirmation_message)

    raise dash.exceptions.PreventUpdate


@app.callback(
    Output({"type": "starred-item", "label": ALL}, "style"),
    Input({"type": "starred-item", "label": ALL}, "n_clicks"),
)
def update_styles(starred):
    """
    Callback to highlight a clicked starred measurement

    Args:
        starred: Unused, the number of clicks for all items

    Returns:

    """

    triggered_id = ctx.triggered_id

    active_style = {"cursor": "pointer", "backgroundColor": "#fff3b0", "margin": "5px"}
    base_style = {"cursor": "pointer", "backgroundColor": "#ffffff", "margin": "5px"}

    if not triggered_id:
        return [base_style for item in ctx.outputs_list]

    if triggered_id.get("type") == "starred-item":
        active_label = triggered_id["label"]

    style_list = []
    for item in ctx.outputs_list:
        label = item["id"]["label"]
        if label == active_label:
            style_list.append(active_style)
        else:
            style_list.append(base_style)

    return style_list


@app.callback(
    Output({"type": "starred-list", "index": MATCH}, "children"),
    Input({"type": "starred-store", "index": MATCH}, "data"),
    prevent_initial_call=True,
)
def display_starred(starred):
    if not starred:
        return "No starred items yet."

    list_items = []
    for item in starred:
        style = {"cursor": "pointer", "margin": "5px"}
        list_item = html.Li(
            f"⭐ {item}",
            id={"type": "starred-item", "label": item},
            style=style,
        )
        list_items.append(list_item)

    u_list = html.Ul(list_items)

    return u_list


@app.callback(
    Output({"type": "tab-content", "index": MATCH}, "children"),
    Input({"type": "tabs", "index": MATCH}, "value"),
    Input({"type": "outer-selector", "index": MATCH}, "value"),
    Input({"type": "intermediate-selector", "index": MATCH}, "value"),
    Input({"type": "inner-selector", "index": MATCH}, "value"),
    Input({"type": "starred-item", "label": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def update_tab(tab: str, outer: str, inter: str, inner: str, starred):
    """
    Callback to update the tab content with the calibration image and qubit data

    Args:
        tab: Whether it is the image or the json tab
        outer: Outer folder with the measurement date
        inter: Intermediate folder with the calibration run
        inner: Inner folder with the qubit measurement

    Returns:

    """

    triggered_id = ctx.triggered_id
    triggered = ctx.triggered

    clicked = triggered_id and "label" in triggered_id
    if not (outer and inter and inner) and not clicked:
        return "Please make all selections."

    if triggered_id and triggered_id.get("type") == "starred-item":
        folder_path = os.path.join(DATA_DIR, triggered_id["label"])
    else:
        folder_path = os.path.join(DATA_DIR, outer, inter, inner)

    if tab == "image":
        image_names = []
        for file in os.listdir(folder_path):
            if file.endswith(".png") and "preview" in file:
                image_names.append(file)
        if len(image_names) > 1:
            # the regular expression matches the numerical identifier
            # when the folder contains multiple images, eg the identifier 11 here:
            # measurement_11_preview.png
            # this identifier is used to sort the image names list
            image_names.sort(
                key=lambda s: int(re.match(r".*_(\d+)_preview.png", s).group(1))
            )
        graph_previews = []
        for image_local_path in image_names:
            image_path = os.path.join(folder_path, image_local_path)
            encoded = base64.b64encode(open(image_path, "rb").read()).decode()
            html_image_element = html.Img(
                src=f"data:image/png;base64,{encoded}", style={"maxWidth": "100%"}
            )
            graph_previews.append(html_image_element)
        if graph_previews:
            return html.Div(graph_previews)
        return "No image found."

    elif tab == "json":
        json_box_style = {
            "flex": "1",
            "minWidth": "300px",  # responsive: wrap if too narrow
            "overflow": "auto",
            "padding": "10px",
            "border": "1px solid #ddd",
            "borderRadius": "6px",
        }
        for file in os.listdir(folder_path):
            if file.endswith(".json") and "qoi" not in file:
                with open(os.path.join(folder_path, file)) as f:
                    data = json.load(f)
                columns = []
                for key in data:
                    element_json_box = html.Div(
                        style=json_box_style,
                        children=[
                            html.H4(key),
                            DashRenderjson(
                                id=f"json-view-{key}",
                                data=data[key]["data"],
                                max_depth=1,  # collapse nested content initially
                                invert_theme=True,
                            ),
                        ],
                    )
                    columns.append(element_json_box)
                json_view = html.Div(
                    columns,
                    style={
                        "display": "flex",
                        "flexWrap": "wrap",  # wrap when many keys
                        "gap": "20px",
                    },
                )
                return json_view

        return "No JSON file found."

    return "Invalid tab."


@app.callback(
    [
        Output({"type": "full-dataset", "index": MATCH}, "data"),
        Output({"type": "element-selector", "index": MATCH}, "options"),
    ],
    Input({"type": "inner-selector", "index": MATCH}, "value"),
    Input({"type": "intermediate-selector", "index": MATCH}, "value"),
    Input({"type": "outer-selector", "index": MATCH}, "value"),
)
def display_element_selector(
    selected_inner: str, selected_intermediate: str, selected_outer: str
):
    if selected_outer and selected_intermediate and selected_inner:

        inner_path = os.path.join(
            DATA_DIR, selected_outer, selected_intermediate, selected_inner
        )
        hdf5_files = [f for f in os.listdir(inner_path) if f.endswith(".hdf5")]

        if hdf5_files:
            hdf5_path = os.path.join(inner_path, hdf5_files[0])
            try:
                ds = xr.open_dataset(hdf5_path)
                elements_attr = ds.attrs.get("elements", [])
                if isinstance(elements_attr, str):
                    elements_attr = [elements_attr]
                element_options = (
                    [{"label": el, "value": el} for el in elements_attr]
                    if isinstance(elements_attr, list)
                    else []
                )
                ds_dict = ds.to_dict()
                ds_json = json.dumps(ds_dict)

                return [ds_json, element_options]
                # return f"HDF5 File: {hdf5_files[0]}", ds_json, element_options
            except Exception as e:
                return [json.dumps({"error": str(e)}), []]
                # return f"HDF5 File: {hdf5_files[0]}", json.dumps({"error": str(e)}), []
        return [{}, []]
        # return "No HDF5 file found.", "{}", []
    return [{}, []]
    # return "", "{}", []


@app.callback(
    Output({"type": "dataset-container", "index": MATCH}, "children"),
    Output({"type": "y-dim-selector", "index": MATCH}, "options"),
    Input({"type": "element-selector", "index": MATCH}, "value"),
    State({"type": "full-dataset", "index": MATCH}, "data"),
)
def filter_dataset_by_element(selected_elements: list, dataset_json: str):
    if not selected_elements or not dataset_json:
        return ["", []]
    try:
        if isinstance(selected_elements, str):
            selected_elements = [selected_elements]
        ds = xr.Dataset.from_dict(json.loads(dataset_json))
        displays = []
        y_dim_options = set()
        styles = dict(
            mirror=True,
            ticks="outside",
            showline=True,
            linecolor="black",
            gridcolor="lightgrey",
        )
        for el in selected_elements:
            filtered_ds = ds.filter_by_attrs(element=el)
            if "ReIm" in filtered_ds.dims:
                attrs = filtered_ds.attrs
                filtered_ds = filtered_ds.isel(ReIm=0) + 1j * filtered_ds.isel(ReIm=1)
                filtered_ds.attrs = attrs

            for var in filtered_ds.data_vars:
                da = filtered_ds[var]
                if da.ndim == 1:
                    fig = px.line(
                        x=da.coords[da.dims[0]], y=abs(da), title=var, markers=True
                    )
                    fig.update_layout(plot_bgcolor="white")
                    fig.update_xaxes(styles)
                    fig.update_yaxes(
                        mirror=True,
                        ticks="outside",
                        showline=True,
                        linecolor="black",
                        gridcolor="lightgrey",
                    )
                    displays.append(
                        dcc.Graph(
                            figure=fig,
                            style={"border": "1px solid #ccc", "padding": "10px"},
                        )
                    )
                elif da.ndim == 2:
                    if any(["freq" in str(coord) for coord in da.coords]):
                        data = abs(da)
                    else:
                        data = abs(da.T)
                    fig = px.imshow(
                        data, color_continuous_scale="RdBu_r", origin="lower"
                    )
                    displays.append(
                        dcc.Graph(
                            figure=fig,
                            style={"border": "1px solid #ccc", "padding": "10px"},
                        )
                    )
                    for dim in da.dims:
                        y_dim_options.add(dim)
        return [displays, [{"label": d, "value": d} for d in y_dim_options]]
    except Exception as e:
        return [[f"Error filtering dataset: {e}"], []]

@app.callback(
    Output({"type": "outer-selector", "index": MATCH}, "value"),
    State({"type": "outer-selector", "index": MATCH}, "value"),
    Input({"type": "starred-item", "label": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def reset_outer_on_clicked_starred(inter_value: str, n_clicks):
    """
    Clears the outer (date) selection when a starred item is clicked.
    """

    return None  # This clears the inner folder selection

@app.callback(
    Output({"type": "inner-selector", "index": MATCH}, "value"),
    Input({"type": "intermediate-selector", "index": MATCH}, "value"),
    Input({"type": "starred-item", "label": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def reset_inner_on_inter_change(inter_value: str, n_clicks):
    """
    prevents callback errors when the inner (node measurement)
    folder has changed but not the intermediate (calibration chain folder).
    Also clears the selection when a starred item is clicked.
    """

    return None  # This clears the inner folder selection


@app.callback(
    Output({"type": "intermediate-selector", "index": MATCH}, "value"),
    Input({"type": "outer-selector", "index": MATCH}, "value"),
    Input({"type": "starred-item", "label": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def reset_intermediate_on_outer_change(inter_value: str, n_clicks):
    """
    prevents callback errors when the intermediate (calibration chain folder)
    folder has changed but not the outer (date folder).
    Also clears the selection when a starred item is clicked.
    """
    return None  # This clears the intermediate folder selection


@app.callback(
    Output(
        {"type": "dataset-container", "index": MATCH}, "children", allow_duplicate=True
    ),
    Input({"type": "y-dim-selector", "index": MATCH}, "value"),
    State({"type": "element-selector", "index": MATCH}, "value"),
    State({"type": "full-dataset", "index": MATCH}, "data"),
    prevent_initial_call=True,
)
def plot_y_slice(y_dim_value: str, selected_elements: str, dataset_json: str):
    if not selected_elements or not dataset_json or not y_dim_value:
        return ""
    try:
        if isinstance(selected_elements, str):
            selected_elements = [selected_elements]
        ds = xr.Dataset.from_dict(json.loads(dataset_json))
        displays = []
        for el in selected_elements:
            filtered_ds = ds.filter_by_attrs(element=el)
            if "ReIm" in filtered_ds.dims:
                attrs = filtered_ds.attrs
                filtered_ds = filtered_ds.isel(ReIm=0) + 1j * filtered_ds.isel(ReIm=1)
                filtered_ds.attrs = attrs

            for var in filtered_ds.data_vars:
                da = filtered_ds[var]
                if da.ndim == 2 and y_dim_value in da.dims:
                    for val in da[y_dim_value].values:
                        line = da.sel({y_dim_value: val})
                        fig = px.line(
                            x=line.coords[line.dims[0]],
                            y=abs(line),
                            title=f"{var} @ {y_dim_value}={val}",
                            markers=True,
                        )
                        fig.update_layout(plot_bgcolor="white")
                        fig.update_xaxes(
                            mirror=True,
                            ticks="outside",
                            showline=True,
                            linecolor="black",
                            gridcolor="lightgrey",
                        )
                        fig.update_yaxes(
                            mirror=True,
                            ticks="outside",
                            showline=True,
                            linecolor="black",
                            gridcolor="lightgrey",
                        )
                        displays.append(
                            dcc.Graph(
                                figure=fig,
                                style={"border": "1px solid #ccc", "padding": "10px"},
                            )
                        )
        return displays
    except Exception as e:
        return [f"Error plotting y slice: {e}"]


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8050
    app.run(debug=True, port=port)
