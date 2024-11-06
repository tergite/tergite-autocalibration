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
Username
- Can be prefilled

Root dir
- Can be prefilled

- Data dir and config dir can be prefilled as well

- Load a configuration package? (later)

cluster ip
- Can be found by search
- cluster name as well (we should set meaningful cluster names)

redis port
- check whether there is a redis instance running?
- if not offer the option to start one?

Do you want to see plots?
- plotting variable


Then we need this view with the qubits
- input of the qubits

- cluster modules
- we can identify which ones are readout and which ones are drive

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
right_pane = urwid.Filler(output_text, valign="top")


# ------------------------------------------------------------
# This function is called to update the view on the right side
def refresh_dot_env_output():
    # Format the current state to display on the right side
    output_ = "This is the output written to the .env file:\n"
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

    button_ = urwid.Button("Submit")
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

    button_ = urwid.Button("Submit")
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


def on_redis_select(_, option_):
    state["REDIS_PORT"] = option_
    refresh_dot_env_output()


# -------------
# INITIAL SETUP
# -------------
left_panel.original_widget = input_default_prefix()
refresh_dot_env_output()  # Initialize output display with the current state
layout = urwid.Columns([("weight", 1, left_panel), ("weight", 1, right_pane)])


def main():
    global main_loop
    main_loop = urwid.MainLoop(layout, palette=[("reversed", "standout", "")])
    main_loop.run()
