from __future__ import annotations

import dataclasses
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence, Mapping

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDesktopWidget
from quantify_core.data.handling import set_datadir
from quantify_core.data.types import TUID

from quantifiles.path import load_icon
from quantifiles.data import (
    get_results_for_date,
    safe_load_dataset,
    get_all_dates_with_measurements,
)
from quantifiles.plot.autoplot import autoplot
from quantifiles.watcher import TodayFolderMonitor

logger = logging.getLogger(__name__)


class DateList(QtWidgets.QListWidget):
    dates_selected = QtCore.pyqtSignal(list)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self.setSelectionMode(QtWidgets.QListView.ExtendedSelection)
        self.itemSelectionChanged.connect(self.date_selection_changed)

    @QtCore.pyqtSlot(list)
    def update_date_list(self, dates: Sequence[str]) -> None:
        # Add new dates to the list
        for d in dates:
            if not self.findItems(d, QtCore.Qt.MatchExactly):
                self.insertItem(0, d)

        # Remove dates that are no longer in the list
        i = self.count() - 1
        while i >= 0:
            elem = self.item(i)
            if elem is not None and elem.text() not in dates:
                self.takeItem(i)
                del elem
            i -= 1

        # Sort the list in descending order
        self.sortItems(QtCore.Qt.DescendingOrder)

    @QtCore.pyqtSlot()
    def date_selection_changed(self) -> None:
        selection = [item.text() for item in self.selectedItems()]
        self.dates_selected.emit(selection)


class ExperimentList(QtWidgets.QTreeWidget):
    """A widget that displays a list of experiments for the selected dates."""

    # Define the columns to display in the tree view
    cols = ["TUID", "Name", "Date", "Time", "Keywords"]

    # Define signals emitted by this widget
    experiment_selected = QtCore.pyqtSignal(str)
    experiment_activated = QtCore.pyqtSignal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        # Set the number of columns and their labels
        self.setColumnCount(len(self.cols))
        self.setHeaderLabels(self.cols)

        # Connect signals to corresponding slots
        self.itemSelectionChanged.connect(self.select_experiment)
        self.itemActivated.connect(self.activate_experiment)

        # Set up context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    @QtCore.pyqtSlot(QtCore.QPoint)
    def show_context_menu(self, position: QtCore.QPoint) -> None:
        """
        Show a context menu when the user right-clicks on an item in the tree.
        """
        # Get the index and item at the given position
        model_index = self.indexAt(position)
        item = self.itemFromIndex(model_index)
        assert item is not None

        # Create the context menu
        menu = QtWidgets.QMenu()

        copy_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogSaveButton)
        copy_action = menu.addAction(copy_icon, "Copy")

        # Execute the selected action
        action = menu.exec_(self.mapToGlobal(position))
        if action == copy_action:
            QtWidgets.QApplication.clipboard().setText(item.text(model_index.column()))

    def add_experiment(self, tuid: TUID | str, **vals: str) -> None:
        """
        Add a new experiment to the tree.

        Args:
            tuid: The TUID of the experiment.
            vals: The values to display in the tree.
        """
        # Create a new tree widget item with the specified values.
        item = QtWidgets.QTreeWidgetItem(
            [
                str(tuid),
                vals.get("name", ""),
                vals.get("date", ""),
                vals.get("time", ""),
                vals.get("keywords_", ""),
            ]
        )
        self.addTopLevelItem(item)

    def set_experiments(self, selection: Mapping[str, Mapping[str, str]]) -> None:
        # Clear the existing items in the list
        self.clear()

        # disable sorting before inserting values to avoid performance hit
        self.setSortingEnabled(False)

        # Add each experiment as a new item in the list
        for tuid, record in selection.items():
            self.add_experiment(tuid, **record)

        # Re-enable sorting and resize the columns
        self.setSortingEnabled(True)
        for i in range(len(self.cols)):
            self.resizeColumnToContents(i)

    def update_experiments(self, selection: Mapping[str, Mapping[str, str]]) -> None:
        new_item_found = False

        # Update each experiment in the list
        for tuid, record in selection.items():
            items = self.findItems(str(tuid), QtCore.Qt.MatchExactly)

            # If the experiment is not already in the list,
            # add it to the list
            if not items:
                self.setSortingEnabled(False)
                self.add_experiment(tuid, **record)
                new_item_found = True
            else:
                raise logger.error(f"More than one dataset found with tuid: " f"{tuid}")

        if new_item_found:
            self.setSortingEnabled(True)
            for i in range(len(self.cols)):
                self.resizeColumnToContents(i)

    @QtCore.pyqtSlot()
    def select_experiment(self) -> None:
        selection = self.selectedItems()
        if len(selection) == 0:
            return

        tuid = selection[0].text(0)
        self.experiment_selected.emit(tuid)

    @QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem, int)
    def activate_experiment(self, item: QtWidgets.QTreeWidgetItem, _: int) -> None:
        tuid = item.text(0)
        self.experiment_activated.emit(tuid)


class DataDirLabel(QtWidgets.QLabel):
    """
    A label that displays the currently selected data directory.

    Args:
        datadir (str): The path to the currently selected data directory.
        parent (QtWidgets.QWidget, optional): The parent widget of the label.
    """

    def __init__(self, datadir: str, parent: QtWidgets.QWidget | None = None):
        """
        Initializes the DataDirLabel widget.

        Args:
            datadir (str): The path to the currently selected data directory.
            parent (QtWidgets.QWidget, optional): The parent widget of the label.
        """
        super().__init__(parent)

        self.update_datadir(datadir)

    def update_datadir(self, datadir: str) -> None:
        """
        Updates the label to display the current data directory.

        Args:
            datadir (str): The path to the currently selected data directory.
        """
        if datadir is None:
            self.setText("No data directory selected")
        else:
            self.setText(f"Data directory: {datadir}")


class DataDirInspector(QtWidgets.QMainWindow):
    """
    A window that displays the contents of a data directory.

    This is the main window of the application.
    """

    _WINDOW_TITLE: str = "Quantifiles | Quantify dataset browser"
    _DATE_LIST_REFRESH_INTERVAL: int = 2000

    # Signal that is emitted when a new data directory is selected
    new_datadir_selected = QtCore.pyqtSignal(str)

    def __init__(
        self,
        datadir: str | None = None,
        auto_open_plots: bool = False,
        parent: QtWidgets.QWidget | None = None,
    ):
        super().__init__(parent)

        self.datadir = datadir
        self._selected_dates: tuple[str, ...] = ()
        self.plots = []
        self._auto_open_plots = auto_open_plots

        self.setWindowTitle(self._WINDOW_TITLE)

        # create widgets
        self.experiment_list = ExperimentList()
        self.date_list = DateList()

        # create splitter for widgets
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.date_list)
        splitter.addWidget(self.experiment_list)
        splitter.setSizes([80, 820])

        # set splitter as central widget
        self.setCentralWidget(splitter)

        # create data directory label and toolbar
        self.datadir_label = QtWidgets.QLabel(datadir)
        self.toolbar = self.addToolBar("Data Directory")
        self.toolbar.addWidget(self.datadir_label)
        self.toolbar.setMovable(False)

        # create menu bar
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")

        # create Open and Reload actions
        open_action = QtWidgets.QAction("&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.configure_datadir)
        file_menu.addAction(open_action)

        reload_action = QtWidgets.QAction("&Reload", self)
        reload_action.setShortcut("R")
        reload_action.triggered.connect(self.reload_datadir)
        file_menu.addAction(reload_action)

        # create Exit action
        exit_action = QtWidgets.QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        self._today_folder_monitor = TodayFolderMonitor(self.datadir, parent=self)
        self._date_list_timer = QtCore.QTimer()
        self._date_list_timer.timeout.connect(self._update_date_list)
        self._date_list_timer.start(self._DATE_LIST_REFRESH_INTERVAL)

        # set window size
        screen = QDesktopWidget().screenGeometry()
        self.resize(int(screen.width() * 0.6), int(screen.height() * 0.6))

        # connect signals and slots
        self.experiment_list.experiment_activated.connect(self.open_plots)
        self.date_list.dates_selected.connect(self.set_date_selection)
        self.new_datadir_selected.connect(self.update_datadir)
        self._today_folder_monitor.new_measurement_found.connect(
            self._on_new_measurement
        )

        # update data directory if provided
        if datadir is not None:
            self.update_datadir()

    @QtCore.pyqtSlot(str)
    def open_plots(self, tuid: str) -> None:
        # Load the dataset and create a plot
        ds = safe_load_dataset(tuid)
        p = autoplot(ds)

        # Add the plot to the list of plots and show it
        self.plots.append(p)
        p.show()

    @QtCore.pyqtSlot()
    def reload_datadir(self) -> None:
        # Update the datadir label and set the datadir
        self.datadir_label.setText(self.datadir)
        set_datadir(self.datadir)

        self._update_date_list()
        self._today_folder_monitor.set_datadir(self.datadir)

        # Reselect the dates to update
        self.set_date_selection(self._selected_dates)

    @QtCore.pyqtSlot()
    def _update_date_list(self) -> None:
        dates = get_all_dates_with_measurements()
        date_strings = [date.strftime("%Y-%m-%d") for date in dates]
        self.date_list.update_date_list(date_strings)

    @QtCore.pyqtSlot()
    def configure_datadir(self) -> None:
        # Open a file dialog to select the data directory
        curdir = self.datadir if self.datadir is not None else os.getcwd()
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Open quantify data directory",
            curdir,
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )

        # If a directory was selected, update the datadir
        if path:
            self.datadir = path
            self.new_datadir_selected.emit(path)

    def update_datadir(self) -> None:
        self.reload_datadir()
        self.date_list.setCurrentRow(0)

    @QtCore.pyqtSlot(str)
    def _on_new_measurement(self, tuid: str):
        self.set_date_selection(self._selected_dates)
        if self._auto_open_plots:
            self.open_plots(tuid)

    @QtCore.pyqtSlot(list)
    def set_date_selection(self, dates: Sequence[str]) -> None:
        if len(dates) > 0:
            selection_dict = {}
            for date in dates:
                results = get_results_for_date(datetime.strptime(date, "%Y-%m-%d"))
                selection_dict.update(
                    {tuid: dataclasses.asdict(data) for tuid, data in results.items()}
                )

            self.experiment_list.set_experiments(selection_dict)
            self._selected_dates = tuple(dates)
        else:
            self._selected_dates = ()
            self.experiment_list.clear()


def main(
    datadir: str | Path | None = None, log_level: int | str = logging.WARNING
) -> None:
    """
    The main function for the Quantifiles application. Initializes the Qt application,
    sets the application name and icon, creates the main window with the specified data
    directory (or None if not provided), and starts the event loop.

    Parameters
    ----------
    datadir: str | Path | None, optional (default: None) Path to the data directory to open on launch. If None, the
    user will have to select a data directory manually.
    log_level: int | str, optional (default: logging.WARNING) The logging level to use. Can be an integer or a string.

    Returns
    -------
        None.
    """
    app = QtWidgets.QApplication([])
    logging.basicConfig(level=log_level)
    app.setApplicationName("Quantifiles")
    app.setWindowIcon(load_icon("icon.png"))

    win = DataDirInspector(datadir=datadir)
    win.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        appinstance = QtWidgets.QApplication.instance()
        assert appinstance is not None
        appinstance.exec_()


if __name__ == "__main__":
    main(r"C:\Users\Damie\PycharmProjects\quantifiles\test_data")
