import os

from tergite_autocalibration.config.globals import ENV
from tergite_autocalibration.config.package import ConfigurationPackage
from tergite_autocalibration.tools.cli.config import load

if __name__ == "__main__":

    # Some function to get the number of qubits or the qubits themselves

    # Load the default configuration package
    load(template=".default")

    # Create a configuration package object for easier handling
    configuration_package = ConfigurationPackage.from_toml(
        os.path.join(ENV.config_dir, "configuration.meta.toml")
    )

    # Insert the template values for device configuration
    configs_to_update = ["device_config", "run_config"]

    # Iterate over the configurations to update
    # Note: This can be looped at the moment, since there is a very simple logic behind updating
    #       the configurations. It can also be solved in a more advanced way and more specific for
    #       each single configuration file, but right now the only necessary parameter is the list
    #       of qubits.
    for config_name in configs_to_update:

        # Get the path to the configuration template
        config_template_path = os.path.join(
            configuration_package.misc_filepaths["j2_templates"],
            f"{config_name}.j2",
        )

        # Insert the template values for run configuration


        # Write the configuration values to the .toml files
        config_output_file_path = configuration_package.config_files[config_name]
