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

"""
- Data dir and config dir can be prefilled as well

- Load a configuration package? (later)


device templates
- we should have template for the 25 qubit chip
- then you can assign the qubits that you want to use?

Other templates?
- load from data/devices?
Do you want to change some of the default values?

to be thought through
- VNA frequencies
- Mixer calibration

"""

# TODO: This file is gonna be renamed later

import urwid

from tergite_autocalibration.tools.cli.config import helpers
from tergite_autocalibration.tools.cli.config.parsers import parse_input_qubit

# Trying to follow a model view controller pattern
# Everything in one file, because Python would create some circular imports otherwise

# -------------
# Model section
# -------------
state = {}

# -----------------------
# View-Controller section
# -----------------------

# Layout looks a bit like this:
# Left side     | Right side
# Inputs        | Outputs

left_panel = urwid.WidgetPlaceholder(urwid.Pile([]))


output_text = urwid.Text("")
right_panel = urwid.Filler(output_text, valign="top")


# ------------------------------------------------------------
# This function is called to update the view on the right side
def refresh_dot_env_output():
    # Format the current state to display on the right side
    output_ = ""
    for key_, value_ in state.items():
        output_ += f"{key_}: {value_}\n"
    output_text.set_text(output_)


# --------------
# DEFAULT_PREFIX
# --------------
def input_default_prefix():
    caption_text_ = urwid.Text(
        "Please enter your DEFAULT_PREFIX.\n"
        "The default prefix is used for example in logfiles.\n"
        "It could be your username or anything related to identify this installation."
    )
    input_ = urwid.Edit("DEFAULT_PREFIX: ", helpers.get_username())

    button_ = urwid.Button("OK")
    urwid.connect_signal(button_, "click", on_submit_default_prefix, input_)
    default_prefix_button_ = urwid.AttrMap(button_, None, focus_map="reversed")

    return urwid.Pile([caption_text_, urwid.Divider(), input_, default_prefix_button_])


def on_submit_default_prefix(_, edit_):
    # TODO: validate input
    state["DEFAULT_PREFIX"] = edit_.get_edit_text()
    refresh_dot_env_output()
    input_root_dir()


# --------
# ROOT_DIR
# --------
def input_root_dir():
    caption_text_ = urwid.Text(
        "Please enter the ROOT_DIR.\n"
        "The root directory defines the directory from where the relative paths "
        "to the config and output files are generated.\n"
        "The default is the current directory you are in."
    )
    input_ = urwid.Edit("ROOT_DIR: ", helpers.get_cwd())

    button_ = urwid.Button("OK")
    urwid.connect_signal(button_, "click", on_submit_root_dir, input_)
    default_prefix_button_ = urwid.AttrMap(button_, None, focus_map="reversed")

    # Update left panel
    left_panel.original_widget = urwid.Pile(
        [caption_text_, urwid.Divider(), input_, default_prefix_button_]
    )


def on_submit_root_dir(_, edit_):
    # TODO: validate whether path exists
    state["ROOT_DIR"] = edit_.get_edit_text()
    refresh_dot_env_output()
    input_cluster_ip()


# ----------
# CLUSTER_IP
# ----------
def input_cluster_ip():
    caption_text_ = urwid.Text(
        "Please select the cluster to be used.\n"
        "You can choose from all clusters that are connected or add a dummy cluster."
    )
    options_ = helpers.get_available_clusters()
    choices_ = [urwid.Divider()]

    # Add the list of cluster tuples, the tuples are of form:
    # (cluster_ip: str, cluster_name: str, firmware_version: str)
    for option_ in options_:
        option_str_ = f"{option_[0]} - {option_[1]} ({option_[2]})"
        button_ = urwid.Button(option_str_)
        urwid.connect_signal(button_, "click", on_cluster_select, option_)
        choices_.append(urwid.AttrMap(button_, None, focus_map="reversed"))

    # Update left panel
    left_panel.original_widget = urwid.Pile([caption_text_] + choices_)


# Function to handle multi-choice selection and update global state
def on_cluster_select(_, option_):
    state["CLUSTER_IP"] = option_[0]
    refresh_dot_env_output()
    input_redis_port()


# ----------
# REDIS_PORT
# ----------
def input_redis_port():
    caption_text_ = urwid.Text(
        "Please enter the port for your redis to be used.\n"
        "You can choose the ports in the list below or enter the port manually.\n"
        "If you enter the port manually, please make sure to start a redis instance."
    )
    options_ = helpers.get_available_redis_instances()
    choices_ = [urwid.Divider()]

    # Add the list of redis instances
    for option_ in options_:
        button_ = urwid.Button(option_)
        urwid.connect_signal(button_, "click", on_redis_select, option_)
        choices_.append(urwid.AttrMap(button_, None, focus_map="reversed"))

    input_ = urwid.Edit("REDIS_PORT: ", "6379")

    submit_button_ = urwid.Button("Set redis port")
    urwid.connect_signal(submit_button_, "click", on_redis_submit, input_)
    redis_port_button_ = urwid.AttrMap(submit_button_, None, focus_map="reversed")

    # Update left panel
    left_panel.original_widget = urwid.Pile(
        [caption_text_] + choices_ + [urwid.Divider(), input_, redis_port_button_]
    )


def on_redis_submit(_, edit_):
    state["REDIS_PORT"] = edit_.get_edit_text()
    refresh_dot_env_output()
    input_plotting()


def on_redis_select(_, option_):
    state["REDIS_PORT"] = option_
    refresh_dot_env_output()
    input_plotting()


# ----------
# REDIS_PORT
# ----------
def input_plotting():
    caption_text_ = urwid.Text(
        "Do you want to see plots?\n"
        "Note: You can only see plots if you are having a graphical interface or X11 port forwarding activated."
    )
    plotting_yes_button_ = urwid.Button("Yes")
    urwid.connect_signal(plotting_yes_button_, "click", on_plotting_submit, True)
    plotting_yes_button_ = urwid.AttrMap(
        plotting_yes_button_, None, focus_map="reversed"
    )
    plotting_no_button_ = urwid.Button("No")
    urwid.connect_signal(plotting_no_button_, "click", on_plotting_submit, False)
    plotting_no_button_ = urwid.AttrMap(plotting_no_button_, None, focus_map="reversed")

    # Update left panel
    left_panel.original_widget = urwid.Pile(
        [caption_text_, urwid.Divider(), plotting_yes_button_, plotting_no_button_]
    )


def on_plotting_submit(_, option_):
    state["PLOTTING"] = option_
    refresh_dot_env_output()
    input_qubits()


# --------------------------------------------------------
# This is now the section starting for the run_config.toml
# ------
# qubits
# ------
def input_qubits():
    caption_text_ = urwid.Text(
        "Please enter the qubits you want to use.\n"
        "You can enter by space (q01 q02 q03 ...), comma (q01,q02,q03), comma and space (q01, q02, q03) "
        "or by a range (q01-q05), or a combination of spaces and ranges."
    )
    input_ = urwid.Edit("qubits: ", "")

    button_ = urwid.Button("OK")
    urwid.connect_signal(button_, "click", on_submit_qubits, input_)
    qubits_button_ = urwid.AttrMap(button_, None, focus_map="reversed")

    left_panel.original_widget = urwid.Pile(
        [caption_text_, urwid.Divider(), input_, qubits_button_]
    )


def on_submit_qubits(_, edit_):
    # Parse and go
    qubit_str_ = edit_.get_edit_text()
    state["qubits"] = parse_input_qubit(qubit_str_)
    refresh_dot_env_output()
    input_cluster_modules()


def input_cluster_modules():
    caption_text_ = urwid.Text(
        "Please select the modules inside the cluster that are used for the calibration."
    )
    options_ = helpers.get_cluster_modules()
    state["cluster_modules"] = []
    choices_ = [urwid.Divider()]

    # Add the list of cluster module tuples, the tuples are of form:
    # (module_name: str, module_type: str)
    for option_ in options_:
        option_str_ = f"{option_[0]} - ({option_[1]})"
        button_ = urwid.Button(option_str_)
        urwid.connect_signal(button_, "click", on_toggle_cluster_modules, option_)
        choices_.append(urwid.AttrMap(button_, None, focus_map="reversed"))

    button_ = urwid.Button("OK")
    urwid.connect_signal(button_, "click", on_submit_cluster_modules)
    cluster_modules_button_ = urwid.AttrMap(button_, None, focus_map="reversed")

    # Update left panel
    left_panel.original_widget = urwid.Pile(
        [caption_text_] + choices_ + [urwid.Divider("-"), cluster_modules_button_]
    )


def on_toggle_cluster_modules(_, option_):
    if option_ in state["cluster_modules"]:
        state["cluster_modules"].remove(option_)
    else:
        state["cluster_modules"].append(option_)
    # Sort output by module name
    state["cluster_modules"] = sorted(state["cluster_modules"], key=lambda x_: x_[0])
    refresh_dot_env_output()


def on_submit_cluster_modules(_):
    refresh_dot_env_output()
    input_qubit_drive_module_mapping()


def input_qubit_drive_module_mapping():
    caption_text_ = urwid.Text(
        "Please create the mapping from the qubits to the modules.\n"
        "On the left side select a qubit and then the respective module on the right side."
    )
    qubit_options_ = state["qubits"]
    qubit_choices_ = [urwid.Divider()]

    for qubit_option_ in qubit_options_:
        option_str_ = f"{qubit_option_}"
        button_ = urwid.Button(option_str_)
        urwid.connect_signal(button_, "click", on_toggle_qubit_in_drive_module_mapping, qubit_option_)
        qubit_choices_.append(urwid.AttrMap(button_, None, focus_map="reversed"))

    module_options_ = state["cluster_modules"]
    module_choices_ = [urwid.Divider()]

    for module_option_ in module_options_:
        option_str_ = f"{module_option_}"
        button_ = urwid.Button(option_str_)
        urwid.connect_signal(button_, "click", on_toggle_module_in_drive_module_mapping, module_option_)
        module_choices_.append(urwid.AttrMap(button_, None, focus_map="reversed"))

    button_ = urwid.Button("OK")
    urwid.connect_signal(button_, "click", on_submit_cluster_modules)
    qubit_drive_module_button_ = urwid.AttrMap(button_, None, focus_map="reversed")

    qubit_input_ = urwid.Pile(qubit_choices_)
    module_input_ = urwid.Pile(module_choices_)

    qubit_map_widget_ = urwid.Columns(
        [
            (
                "weight",
                1,
                urwid.Filler(
                    urwid.Padding(qubit_input_, left=1, right=1),
                    valign="top",
                ),
            ),
            (
                "weight",
                1,
                urwid.Filler(
                    urwid.Padding(module_input_, left=1, right=1),
                    valign="top",
                ),
            ),
        ]
    )

    # Update left panel
    left_panel.original_widget = urwid.Pile(
        [caption_text_, qubit_map_widget_, urwid.Divider(), qubit_drive_module_button_]
    )


def on_toggle_qubit_in_drive_module_mapping():
    pass


def on_toggle_module_in_drive_module_mapping():
    pass


# -------------
# INITIAL SETUP
# -------------
left_panel.original_widget = input_default_prefix()
refresh_dot_env_output()

header = urwid.Filler(
    urwid.Padding(
        urwid.AttrMap(
            urwid.Text(
                "Autocalibration configuration wizard",
                align="left",
            ),
            "bold",
        ),
        left=1,
        right=1,
    ),
    top=1,
    bottom=0,
    valign="top",
)

line = urwid.Filler(
    urwid.Padding(
        urwid.Divider("-"),
        left=1,
        right=1,
    ),
    valign="top",
)

body_layout = urwid.Columns(
    [
        (
            "weight",
            1,
            urwid.Filler(
                urwid.Padding(left_panel, left=1, right=1),
                top=1,
                bottom=1,
                valign="top",
            ),
        ),
        (
            "weight",
            1,
            urwid.Filler(
                urwid.Padding(right_panel, left=1, right=1),
                top=1,
                bottom=1,
                valign="top",
            ),
        ),
    ]
)

layout = urwid.Pile([("pack", header), ("pack", line), ("pack", body_layout)])


def main():
    global main_loop
    main_loop = urwid.MainLoop(layout, palette=[("reversed", "standout", "")])
    main_loop.run()
