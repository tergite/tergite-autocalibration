from jinja2 import Environment, FileSystemLoader


if __name__ == '__main__':


    def generate_resonator_toml(num_qubits, vna_frequency_placeholder=""):
        # Load the template
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template("device_config.j2")

        qubits = ["%02d".format(i) for i in range(num_qubits)]

        # Render the template with values
        output = template.render(qubits=qubits, vna_frequency_placeholder=vna_frequency_placeholder)

        # Write the output to a TOML file
        with open("device_config.toml", "w") as toml_file:
            toml_file.write(output)

        print("TOML configuration generated successfully.")


    # Example usage
    generate_resonator_toml(num_qubits=5, vna_frequency_placeholder="")
