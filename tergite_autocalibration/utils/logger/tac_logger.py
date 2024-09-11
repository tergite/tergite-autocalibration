# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import logging.handlers

# setting up the logger
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)

syslog = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s \u25c6 %(filename)s \u25c6 %(message)s")
syslog.setFormatter(formatter)
logger.addHandler(syslog)
logger.propagate = False
