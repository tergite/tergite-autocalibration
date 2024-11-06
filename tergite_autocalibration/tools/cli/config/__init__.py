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

import typer

config_cli = typer.Typer()


@config_cli.command(help="Get a configuration value.")
def get():
    # Look up configuration value
    # Put it into the clipboard
    pass


@config_cli.command(help="Set a configuration value.")
def set():
    # Validate input
    # Write into configuration
    # Maybe can have a batch version of the command to set all values from a file
    pass


@config_cli.command(help="List available configuration values.")
def show():
    # Show all configuration values
    # What should the inputs be?
    pass


@config_cli.command(help="Run the configuration wizard.")
def wizard():
    import urwid
    from .model import state

    # Placeholder for dynamic left panel
    left_panel = urwid.WidgetPlaceholder(urwid.Pile([]))

    # Output display on the right side to reflect global state
    output_text = urwid.Text("Output will appear here")

    # Function to refresh the output text based on the current state
    def refresh_output():
        # Format the current state to display on the right side
        output = f"Text Input: {state['text_input']}\nSelected Option: {state['selected_option']}"
        output_text.set_text(output)

    # Function to handle submit button click and update global state
    def on_submit(button, edit):
        # Update the state with the entered text
        state["text_input"] = edit.get_edit_text()
        refresh_output()  # Refresh output to reflect updated state
        update_to_multi_choice()  # Transition to multiple-choice options

    # Function to create and display multi-choice input after initial input
    def update_to_multi_choice():
        # Define multiple-choice options
        options = ["Option 1", "Option 2", "Option 3"]
        choices = [urwid.Text("Choose an option:"), urwid.Divider()]

        # Add each option as a button
        for option in options:
            button = urwid.Button(option)
            urwid.connect_signal(button, "click", on_option_select, option)
            choices.append(urwid.AttrMap(button, None, focus_map="reversed"))

        # Replace left panel content with the multiple-choice options
        left_panel.original_widget = urwid.Pile(choices)

    # Function to handle multi-choice selection and update global state
    def on_option_select(button, option):
        # Update the state with the selected option
        state["selected_option"].append(option)
        refresh_output()  # Refresh output to reflect updated state

    # Initial setup: text input and submit button
    input_edit = urwid.Edit("Enter text: ")
    submit_button = urwid.Button("Submit")
    urwid.connect_signal(submit_button, "click", on_submit, input_edit)
    styled_button = urwid.AttrMap(submit_button, None, focus_map="reversed")
    initial_input = urwid.Pile([input_edit, styled_button])

    # Set initial content of the left panel
    left_panel.original_widget = initial_input

    # Right pane to display the current state
    right_pane = urwid.Filler(output_text, valign="top")
    refresh_output()  # Initialize output display with the current state

    # Layout with columns
    layout = urwid.Columns([("weight", 1, left_panel), ("weight", 1, right_pane)])

    # Run the app
    def main():
        global main_loop
        main_loop = urwid.MainLoop(layout, palette=[("reversed", "standout", "")])
        main_loop.run()

    main()


@config_cli.command(help="Run the configuration wizard.")
def mvc():
    from .controller import main

    main()
