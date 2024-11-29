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

from tergite_autocalibration.config.package import ConfigurationPackage

if __name__ == "__main__":
    configuration_package = ConfigurationPackage.from_toml(
        "/Users/stefanhi/repos/tergite-autocalibration/tergite_autocalibration/config/templates/.default/configuration.meta.toml"
    )

    copied_package = configuration_package.copy(
        "/Users/stefanhi/repos/tergite-autocalibration/tergite_autocalibration/config/templates/copied_package"
    )

    copied_package.delete()
    pass
