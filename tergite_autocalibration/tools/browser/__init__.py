# This code is part of Tergite
#
# (C) Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import threading
import webbrowser

from tergite_autocalibration.tools.browser.main import app
from tergite_autocalibration.utils.logging import logger


def start_browser(host: str, port: int):
    try:
        threading.Timer(0.5, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    except Exception as e:
        logger.warning(f"Failed to start browser on http://{host}:{port}")
        logger.warning(e)
    app.run(debug=True, host=host, port=port, use_reloader=False)
