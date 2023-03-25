from __future__ import annotations

import logging
import os
from pathlib import Path

from PyQt5.QtCore import (
    QObject,
    QTimer,
    pyqtSignal,
    QFileSystemWatcher,
    pyqtSlot,
    QTime,
    QDate,
)

from quantifiles.data import safe_load_dataset

logger = logging.getLogger(__name__)


class MidnightTimer(QObject):
    """
    A PyQt object that emits a signal always at midnight.

    Attributes
    ----------
    midnight_signal : pyqtSignal
        A signal that is emitted at midnight.

    timer : QTimer
        A timer that is used to emit the midnight_signal at midnight.

    Methods
    -------
    start_timer()
        Starts the timer.

    stop_timer()
        Stops the timer.

    _msecs_until_midnight()
        Calculates the number of milliseconds until midnight.

    _emit_midnight_signal()
        Emits the midnight_signal and starts the timer again.
    """

    midnight_signal = pyqtSignal()

    def __init__(self):
        """
        Initializes the MidnightTimer object.
        """
        super().__init__()

        # Create a QTimer and connect it to the _emit_midnight_signal function
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._emit_midnight_signal)

        # Start the timer
        self.start_timer()

    def start_timer(self):
        """
        Starts the timer.
        """
        self.timer.start(self._msecs_until_midnight() + 1)

    def stop_timer(self):
        """
        Stops the timer.
        """
        self.timer.stop()

    def _msecs_until_midnight(self) -> int:
        """
        Calculates the number of milliseconds until midnight.

        Returns
        -------
        int
            The number of milliseconds until midnight.
        """
        current_time = QTime.currentTime()
        midnight_time = QTime(23, 59, 59, 999)

        if current_time < midnight_time:
            msecs_until_midnight = current_time.msecsTo(midnight_time)
        else:
            msecs_until_midnight = 1

        return msecs_until_midnight

    def _emit_midnight_signal(self):
        """
        Emits the midnight_signal and starts the timer again.
        """
        self.midnight_signal.emit()
        self.timer.stop()
        self.start_timer()


class SubDirectoryMonitor(QObject):
    """A class that monitors changes to a directory.

    This class uses `QFileSystemWatcher` to monitor changes to the specified
    directory. When a new subdirectory is created in the directory, it emits
    a `dir_created` signal with the path of the new directory.

    Attributes
    ----------
    dir_created (pyqtSignal):
        A signal that is emitted when a new subdirectory is created in the
        monitored directory. The signal argument is a string containing
        the path of the new subdirectory.
    """

    dir_created = pyqtSignal(Path)

    def __init__(self, folder: str | Path) -> None:
        """Constructor for SubDirectoryMonitor.

        Parameters
        ----------
        datadir (str or Path):
            The path to the directory to monitor.
        """
        super().__init__()
        self.folder = str(folder)
        self.fs_watcher = QFileSystemWatcher([self.folder])
        self.fs_watcher.directoryChanged.connect(self._on_dir_change)
        self.subdirectories = set(os.listdir(self.folder))

    @pyqtSlot(str)
    def _on_dir_change(self, path: str) -> None:
        """Callback function for the directoryChanged signal.

        This function is called when a change is detected in the monitored
        directory. It checks if the change is a new subdirectory and emits the
        dir_created signal if it is.

        Parameters
        ----------
        path (str):
            The path of the directory that was changed.
        """
        assert path == self.folder

        subdirectories = set(os.listdir(self.folder))
        new_subdirectories = subdirectories - self.subdirectories
        self.subdirectories = subdirectories

        for new_subdirectory in new_subdirectories:
            new_subdirectory = Path(path) / new_subdirectory
            if new_subdirectory.is_dir():
                self.dir_created.emit(new_subdirectory)

    def set_folder_to_monitor(self, datadir: str | Path) -> None:
        """Change the directory being monitored.

        This function updates the datadir attribute, removes the old directory
        from the file system watcher, adds the new directory to the file system
        watcher, and updates the subdirectories set.

        Parameters
        ----------
        datadir (str or Path):
            The path to the new directory to monitor.
        """
        datadir = str(datadir)
        self.fs_watcher.removePath(self.folder)

        self.fs_watcher.addPath(datadir)
        self.folder = datadir

        self.subdirectories = set(os.listdir(datadir))


class TodayFolderMonitor(QObject):
    """
    A class to monitor a directory for changes in today's folder.

    Parameters
    ----------
    datadir : str or Path
        The path to the directory to be monitored.
    """

    new_measurement_found = pyqtSignal(str)
    today_folder_changed = pyqtSignal(Path)

    def __init__(self, datadir: str | Path, parent: QObject = None):
        """
        Initialize the TodayFolderMonitor.

        Parameters
        ----------
        datadir : str or Path
            The path to the directory to be monitored.
        """
        super().__init__(parent=parent)
        self._datadir: Path = Path(datadir) if isinstance(datadir, str) else datadir

        # Set today's folder based on current date
        self._today_folder = self._datadir / QDate.currentDate().toString("yyyyMMdd")

        # Timer to refresh today's folder
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._configure_today_folder)

        # Monitor for changes in today's folder
        self._folder_monitor = None
        self._configure_today_folder()

        # Timer to refresh today's folder at midnight
        self._midnight_timer = MidnightTimer()
        self._midnight_timer.midnight_signal.connect(self._configure_today_folder)

    @pyqtSlot(str)
    def set_datadir(self, datadir: str | Path):
        """
        Set the data directory to be monitored.

        Parameters
        ----------
        datadir : str or Path
            The path to the directory to be monitored.
        """
        self._datadir = Path(datadir) if isinstance(datadir, str) else datadir
        self._configure_today_folder()

    @pyqtSlot(Path)
    def _on_new_subdir_found(self, subdir: Path):
        """
        Callback function for the new_subdir_found signal.

        Parameters
        ----------
        subdir : Path
            The path to the new subdirectory.
        """
        logger.debug(f"New subdirectory found: {subdir}")
        if not subdir.is_dir():
            return
        tuid = str(subdir.name[:26])
        try:
            _ = safe_load_dataset(tuid)
            logger.info(f"New measurement found: {tuid}")
            self.new_measurement_found.emit(str(tuid))
        except FileNotFoundError:
            pass

    @pyqtSlot()
    def _configure_today_folder(self):
        """
        Configure the TodayFolderMonitor to monitor today's folder.
        """
        # Set today's folder based on current date
        today_folder = self._datadir / QDate.currentDate().toString("yyyyMMdd")

        # Create a SubDirectoryMonitor for today's folder if it exists
        if today_folder.exists():
            self._refresh_timer.stop()
            if today_folder == self._today_folder and self._folder_monitor is not None:
                return

            self._today_folder = today_folder
            logger.info(f"Monitoring today's folder: {self._today_folder}")

            self._folder_monitor = SubDirectoryMonitor(self._today_folder)

            # Connect the dir_created signal from the SubDirectoryMonitor to the new_subdir_found signal
            self._folder_monitor.dir_created.connect(self._on_new_subdir_found)

            # Emit the today_folder_changed signal
            self.today_folder_changed.emit(self._today_folder)
        else:
            self._folder_monitor = None
            self._refresh_timer.start(2000)


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
