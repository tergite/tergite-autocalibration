from __future__ import annotations

import os
from pathlib import Path

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class FileMonitor(QObject):
    """
    Monitor a file for modifications and emit a signal when the file is modified.

    Parameters
    ----------
    path : str
        The path to the file to monitor.
    interval : int
        The interval in milliseconds to check the file for modifications.

    Attributes
    ----------
    file_modified : pyqtSignal
        Signal emitted when the monitored file is modified.
    last_modified : float
        The time the monitored file was last modified.
    """

    file_modified: pyqtSignal = pyqtSignal()

    def __init__(self, path: str | Path, interval: int = 1000) -> None:
        super().__init__()
        self.path: str = str(path)
        self.last_modified: float = os.path.getmtime(path)
        self.timer: QTimer = QTimer()
        self.timer.timeout.connect(self.check_file)
        self._interval: int = interval

    def start(self) -> None:
        """
        Start the file monitor.
        """
        self.timer.start(self._interval)

    def stop(self) -> None:
        """
        Stop the file monitor.
        """
        self.timer.stop()

    def check_file(self) -> None:
        """
        Check if the monitored file has been modified since the last time it was checked.

        If the file has been modified, emit the `file_modified` signal and update
        the `last_modified` attribute.
        """
        current_modified: float = os.path.getmtime(self.path)  # should be thread safe
        if current_modified > self.last_modified:
            self.last_modified = current_modified
            self.file_modified.emit()
