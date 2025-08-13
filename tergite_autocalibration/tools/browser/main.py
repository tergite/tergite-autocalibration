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

import base64
import json
import re
import os

import dash
import plotly.express as px
import xarray as xr
from dash import callback_context, dcc, html
from dash.dependencies import Input, Output, State
from dash.dependencies import MATCH
from dash_renderjson import DashRenderjson

from tergite_autocalibration.config.globals import DATA_DIR
from tergite_autocalibration.tools.browser.layout import (
    generate_selection_layout,
)
from tergite_autocalibration.tools.browser.utils import scan_folders

folder_structure = scan_folders(DATA_DIR)

app = dash.Dash(__name__)

app.title = "Data Browser - Tergite Autocalibration"

app.layout = html.Div(
    [
        dcc.Store(id="folder-data", data=folder_structure),
        dcc.Store(id="selected-2d-variable"),
        html.Button(
            "Refresh Folder Structure",
            id="refresh-button",
            n_clicks=0,
            style={
                "marginRight": "15px",  # spacing to the right
                "padding": "10px 20px",  # bigger button
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
                "marginRight": "15px",
                "padding": "10px",
                "fontSize": "18px",
                "width": "250px",
            },
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
    Output({"type": "intermediate-selector", "index": MATCH}, "options"),
    Input({"type": "outer-selector", "index": MATCH}, "value"),
    Input("folder-data", "data"),
)
def update_intermediate_folders(selected_outer: str, folder_data: dict):
    """
    Callback to update the intermediate folders with the selection for the calibration runs

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
    ctx = callback_context
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
            [
                "Filter applied: ",
                styled_text_span,
            ],
            style={"marginTop": "10px"},
        )
        return (scan_folders(DATA_DIR, filter_text=filter_text), confirmation_message)

    raise dash.exceptions.PreventUpdate


@app.callback(
    Output({"type": "tab-content", "index": MATCH}, "children"),
    Input({"type": "tabs", "index": MATCH}, "value"),
    Input({"type": "outer-selector", "index": MATCH}, "value"),
    Input({"type": "intermediate-selector", "index": MATCH}, "value"),
    Input({"type": "inner-selector", "index": MATCH}, "value"),
)
def update_tab(tab: str, outer: str, inter: str, inner: str):
    """
    Callback to update the tab content with the calibration image and qubit data

    Args:
        tab: Whether it is the image or the json tab
        outer: Outer folder with the measurement date
        inter: Intermediate folder with the calibration run
        inner: Inner folder with the qubit measurement

    Returns:

    """

    if not (outer and inter and inner):
        return "Please make all selections."

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
            encoded = base64.b64encode(
                open(os.path.join(folder_path, image_local_path), "rb").read()
            ).decode()
            html_image_element = html.Img(
                src=f"data:image/png;base64,{encoded}", style={"maxWidth": "100%"}
            )
            graph_previews.append(html_image_element)
        if graph_previews:
            return html.Div(graph_previews)
        return "No image found."

    elif tab == "json":
        for file in os.listdir(folder_path):
            if file.endswith(".json"):
                with open(os.path.join(folder_path, file)) as f:
                    data = json.load(f)
                return DashRenderjson(
                    data=data,
                    max_depth=-1,
                    invert_theme=True,
                    # , theme="monokai"
                )
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
    [
        Output(
            {"type": "dataset-container", "index": MATCH},
            "children",
            # allow_duplicate=True,
        ),
        Output({"type": "y-dim-selector", "index": MATCH}, "options"),
    ],
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
        for el in selected_elements:
            filtered_ds = ds.filter_by_attrs(element=el)
            if "ReIm" in filtered_ds.dims:
                attrs = filtered_ds.attrs
                filtered_ds = filtered_ds.isel(ReIm=0) + 1j * filtered_ds.isel(ReIm=1)
                filtered_ds.attrs = attrs

            for var in filtered_ds.data_vars:
                da = filtered_ds[var]
                if da.ndim == 1:
                    fig = px.line(x=da.coords[da.dims[0]], y=abs(da), title=var)
                    displays.append(
                        dcc.Graph(
                            figure=fig,
                            style={"border": "1px solid #ccc", "padding": "10px"},
                        )
                    )
                elif da.ndim == 2:
                    for dim in da.dims:
                        y_dim_options.add(dim)
        # return [[{"label": d, "value": d} for d in y_dim_options]]
        return [displays, [{"label": d, "value": d} for d in y_dim_options]]
    except Exception as e:
        # return [[]]
        return [[f"Error filtering dataset: {e}"], []]


@app.callback(
    Output({"type": "inner-selector", "index": MATCH}, "value"),
    Input({"type": "intermediate-selector", "index": MATCH}, "value"),
    prevent_initial_call=True,
)
def reset_inner_on_inter_change(inter_value: str):
    """
    prevents callback errors when the inner (node measurement)
    folder has changed but not the intermediate (calibration chain folder)
    """
    return None  # This clears the inner folder selection


@app.callback(
    Output({"type": "intermediate-selector", "index": MATCH}, "value"),
    Input({"type": "outer-selector", "index": MATCH}, "value"),
    prevent_initial_call=True,
)
def reset_intermediate_on_outer_change(inter_value: str):
    """
    prevents callback errors when the intermediate (calibration chain folder)
    folder has changed but not the outer (date folder)
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
