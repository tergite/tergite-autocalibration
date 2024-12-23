# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
# (C) Copyright Chalmers Next Labs AB 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import logging.handlers

# from tergite_autocalibration.config.globals import ENV


class ExtendedLogger(logging.Logger):
    """
    Adds a custom logger class
    """

    # This is to have a more distinguished logging level.
    # Usually, third-party libraries would also log on logging.INFO, but we want to have some level in between
    # logging.INFO and logging.WARNING, where we do not get spammed by unrelated information.
    STATUS_LEVEL = 25

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.addLevelName(self.STATUS_LEVEL, "STATUS")

    def status(self, message, *args, **kwargs):
        """
        Adds a custom log level for the logger
        This works similar to logging.info() or logging.debug(), just that the level is 25 in this case

        Args:
            message: Message to log

        """
        if self.isEnabledFor(self.STATUS_LEVEL):
            self._log(self.STATUS_LEVEL, message, args, **kwargs)

    def add_console_handler(self, log_level: int = STATUS_LEVEL):
        """
        Adds a console handler to the logger

        Args:
            log_level: Log level for the output on the console

        """
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)

        self.addHandler(console_handler)

    def add_file_handler(
        self, log_level: int = logging.DEBUG, log_file: str = "autocalibration.log"
    ):
        """
        Adds a file handler to the logger

        Args:
            log_level: Log level for the file handler. Defaults to logging.DEBUG to have more granular information
            log_file: Path to log file. Defaults to "autocalibration.log"

        """
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)

        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)

        self.addHandler(file_handler)


# Create a logger
# This is right now an empty logger without handlers
# To use the logger, you have to add the handlers e.g. in tergite_autocalibration.config.globals
logger = ExtendedLogger(__name__)
