# BSD 2-Clause License
#
# Copyright (c) 2023, Damien Crielaard
# All rights reserved.

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

from __future__ import annotations

import dataclasses
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence, Mapping, Tuple

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QImageReader, QPixmap
from PyQt5.QtWidgets import QDesktopWidget, QMessageBox, QAbstractItemView
from quantify_core.data.handling import set_datadir
from quantify_core.data.types import TUID

from tergite_autocalibration.tools.quantifiles.data import (
    safe_load_dataset,
    get_all_dates_with_measurements,
    get_results_by_run,
    get_runs_by_date,
    locate_dataset_path,
)
from tergite_autocalibration.tools.quantifiles.path import load_icon
from tergite_autocalibration.tools.quantifiles.plot.autoplot import autoplot
from tergite_autocalibration.tools.quantifiles.watcher import TodayFolderMonitor
from tergite_autocalibration.utils.logging import logger


class DateList(QtWidgets.QTreeWidget):
    dates_selected = QtCore.pyqtSignal(list)

    cols = ["Date"]

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        # Set the number of columns and their labels
        self.setColumnCount(len(self.cols))
        self.setHeaderLabels(self.cols)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.itemSelectionChanged.connect(self.date_selection_changed)

        self.setSortingEnabled(True)

    @QtCore.pyqtSlot(list)
    def update_date_list(self, dates: Sequence[datetime]) -> None:

        # Remove all items that are not in the list any longer
        existing_dates = []

        i = self.topLevelItemCount()
        while i > 0:
            i = i - 1
            date_ = self.topLevelItem(i).data(0, Qt.UserRole)
            existing_dates.append(date_)
            if date_ not in dates:
                self.takeTopLevelItem(i)

        for date in dates:
            if date not in existing_dates:
                date_str_ = datetime.strftime(date, "%Y-%m-%d")
                item = QtWidgets.QTreeWidgetItem([date_str_])
                item.setData(0, Qt.UserRole, date)
                self.addTopLevelItem(item)

    @QtCore.pyqtSlot()
    def date_selection_changed(self) -> None:
        selection = [item.text(0) for item in self.selectedItems()]
        self.dates_selected.emit(selection)


class RunList(QtWidgets.QTreeWidget):
    """
    A widget to show the calibration run with time and status information.
    """

    # The table shows time and status information e.g. FAILED, SUCCESS or ACTIVE
    cols = ["Time", "Status"]

    # Define signals emitted by the widget
    runs_selected = QtCore.pyqtSignal(list)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        # Set the number of columns and their labels
        self.setColumnCount(len(self.cols))
        self.setHeaderLabels(self.cols)

        self.setSelectionMode(QtWidgets.QListView.ExtendedSelection)
        self.itemSelectionChanged.connect(self.run_selection_changed)

        self.setSortingEnabled(True)

    @QtCore.pyqtSlot(list)
    def update_run_list(
        self, run_time_status_items: Sequence[Tuple[datetime, str]]
    ) -> None:
        """
        Update the tree view with new run time and status items.

        Args:
            run_time_status_items (Sequence[Tuple[str, str]]): List of tuples containing run time and status.
        """

        # Remove all items that are not in the list any longer

        run_times = list(map(lambda x_: x_[0], run_time_status_items))

        existing_runs = []

        i = self.topLevelItemCount()
        while i > 0:
            i = i - 1
            date_ = self.topLevelItem(i).data(0, Qt.UserRole)
            existing_runs.append(date_)
            if date_ not in run_times:
                self.takeTopLevelItem(i)

        for run_time, status in run_time_status_items:
            if run_time not in existing_runs:
                time_str_ = datetime.strftime(run_time, "%H:%M:%S")
                item = QtWidgets.QTreeWidgetItem([time_str_, status])
                item.setData(0, Qt.UserRole, run_time)
                self.addTopLevelItem(item)

    @QtCore.pyqtSlot()
    def run_selection_changed(self) -> None:
        """
        Triggers the signal when one changes the selected runs
        """
        selection = [item.data(0, Qt.UserRole) for item in self.selectedItems()]
        self.runs_selected.emit(selection)


class ExperimentList(QtWidgets.QTreeWidget):
    """A widget that displays a list of experiments for the selected dates."""

    # Define the columns to display in the tree view
    # cols = ["TUID", "Name", "Date", "Time", "Keywords"]
    cols = ["TUID", "Name", "Date", "Time"]

    # Define signals emitted by this widget
    experiment_selected = QtCore.pyqtSignal(str)
    new_experiment_selected = QtCore.pyqtSignal(str)
    experiment_activated = QtCore.pyqtSignal(str, str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        # Set the number of columns and their labels
        self.setColumnCount(len(self.cols))
        self.setHeaderLabels(self.cols)

        # Connect signals to corresponding slots
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.itemSelectionChanged.connect(self.select_experiment)
        # itemActivated means double-clicking or pressing Enter
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
        measurement_name = item.text(1)
        self.experiment_activated.emit(tuid, measurement_name)


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
        self.setWordWrap(True)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )

        font = QtGui.QFont()
        font.setPointSize(8)
        self.setFont(font)

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


class TopBar(QtWidgets.QWidget):
    """
    A class representing a widget for a top bar with a data directory label and a checkbox for live updating.

    Attributes
    ----------
    liveplotting_changed : QtCore.pyqtSignal
        A PyQt signal emitted when the live plotting state changes.

    Methods
    -------
    __init__(datadir: str, liveplotting: bool = False, parent: QtWidgets.QWidget | None = None)
        Constructs a new TopBar object with the given data directory and liveplotting state.
    update_datadir(datadir: str) -> None
        Updates the data directory label with the given value.
    _on_checkbox_changed(state: QtCore.Qt.CheckState) -> None
        A PyQt slot called when the checkbox is changed.
    """

    liveplotting_changed = QtCore.pyqtSignal(bool)

    def __init__(
        self,
        datadir: str,
        liveplotting: bool = False,
        parent: QtWidgets.QWidget | None = None,
    ):
        """
        Constructs a new TopBar object with the given data directory and liveplotting state.

        Parameters
        ----------
        datadir : str
            The data directory string to display.
        liveplotting : bool, optional
            Whether to enable live updating (default is False).
        parent : QtWidgets.QWidget | None, optional
            The parent widget (default is None).
        """

        super().__init__(parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )

        # Create DataDirLabel widget and checkbox
        self.datadir_label = DataDirLabel(datadir)
        checkbox = QtWidgets.QCheckBox("Live updating")
        checkbox.setChecked(liveplotting)
        checkbox.stateChanged.connect(self._on_checkbox_changed)

        # Create horizontal layout and add widgets
        hbox = QtWidgets.QHBoxLayout(self)
        hbox.addWidget(self.datadir_label)
        hbox.addWidget(checkbox, alignment=QtCore.Qt.AlignRight)

        # Set stretch factors, contents margins, and layout
        hbox.setStretchFactor(self.datadir_label, 1)
        hbox.setStretchFactor(checkbox, 0)
        hbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hbox)

    def update_datadir(self, datadir: str) -> None:
        """
        Updates the data directory label with the given value.

        Parameters
        ----------
        datadir : str
            The new data directory string to display.
        """
        self.datadir_label.update_datadir(datadir)

    @QtCore.pyqtSlot(int)
    def _on_checkbox_changed(self, state: QtCore.Qt.CheckState) -> None:
        """
        A PyQt slot called when the checkbox is changed.

        Parameters
        ----------
        state : QtCore.Qt.CheckState
            The new state of the checkbox.
        """
        self.liveplotting_changed.emit(state == QtCore.Qt.Checked)


class ExperimentPreview(QtWidgets.QLabel):
    def __init__(self, datadir: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.datadir = datadir

        # Create label to display image
        # self.image_label = QtWidgets.QLabel()

        # image_label_width = int(screen_width * 0.8)  # Adjust the fraction as needed
        # self.image_label.setFixedWidth(image_label_width)  # Set fixed width for the image label

        self.setWordWrap(True)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )

        # font = QtGui.QFont()
        # font.setPointSize(24)
        # self.setFont(font)

    def display_image(self, image_path):
        # Check if the image file exists
        if QImageReader(image_path).size() == QSize(0, 0):
            self.setText("Image not found")
            return

        # image_reader = QImageReader(image_path)

        # Display the image in the label
        image = QPixmap(image_path)
        # image_reader = QImageReader(image_path)
        # image = image_reader.read()

        # Get the dimensions of the image_label
        label_width = self.width()
        label_height = self.height()
        # self.setFixedSize(label_width, label_height)
        # self.image_label.setFixedSize(image_reader.size().width(), image_reader.size().height())
        # Scale the image while preserving aspect ratio

        # scaled_image = QPixmap.fromImage(image).scaled(label_width, label_height, transformMode=Qt.SmoothTransformation)

        scaled_image = image.scaled(
            label_width,
            label_height,
            transformMode=Qt.SmoothTransformation,
            # label_width, label_height, aspectRatioMode=Qt.KeepAspectRatio
        )

        # Display the scaled image in the label
        self.setPixmap(scaled_image)
        # self.setPixmap(pixmap)

        self.setScaledContents(True)
        self.adjustSize()
        self.setGeometry(100, 100, label_width, label_height)
        # self.setGeometry(5, 5, image.width(), image.height())
        self.show()

    @QtCore.pyqtSlot(str)
    def display_datadir_path(self, tuid: str) -> None:
        folder_path = locate_dataset_path(tuid)

        # if folder_content is None:
        #     self.setText("No data directory selected")
        # else:
        #     self.setText(f"Data directory: {folder_content}")

        files = [
            f
            for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f))
        ]

        # Filter for PNG files
        png_files = [f for f in files if f.lower().endswith(".png")]

        if not png_files:
            self.setText("No PNG image found in the selected folder")
            return

        # Prefer a file with "_preview" in the name; fall back to the first PNG otherwise
        png_file = next((f for f in png_files if "_preview" in f), png_files[0])

        # Assuming one png per file, let's use the first PNG file found in the folder
        image_path = os.path.join(folder_path, png_file)

        self.display_image(image_path)


class DataDirInspector(QtWidgets.QMainWindow):
    """
    A window that displays the contents of a data directory.

    This is the main window of the application.
    """

    _WINDOW_TITLE: str = "Quantifiles | Quantify dataset browser"
    _DATE_LIST_REFRESH_INTERVAL: int = 3000

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
        self._auto_open_plots = auto_open_plots
        self._selected_dates: tuple[str, ...] = ()
        self._selected_runs: tuple[str, ...] = ()
        self.plots = []

        self.setWindowTitle(self._WINDOW_TITLE)

        # create widgets
        self.experiment_list = ExperimentList()
        self.date_list = DateList()
        self.run_list = RunList()
        self.experiment_preview = ExperimentPreview(datadir)

        sub_splitter = QtWidgets.QSplitter()
        sub_splitter.addWidget(self.experiment_list)
        sub_splitter.addWidget(self.experiment_preview)
        sub_splitter.setSizes([350, 650])
        sub_splitter.setOrientation(Qt.Vertical)

        # create splitter for widgets
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.date_list)
        splitter.addWidget(self.run_list)
        splitter.addWidget(sub_splitter)
        splitter.setSizes([150, 200, 915])

        # create data directory label and toolbar
        self.top_bar = TopBar(datadir, liveplotting=auto_open_plots, parent=self)

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

        # create Close all plots action
        close_plots_action = QtWidgets.QAction("&Close all plots", self)
        close_plots_action.setShortcut("X")
        close_plots_action.triggered.connect(self.close_all_plots)
        file_menu.addAction(close_plots_action)

        # create Exit action
        exit_action = QtWidgets.QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Create the timers to automatically refresh
        self._today_folder_monitor = TodayFolderMonitor(self.datadir)
        self._date_list_timer = QtCore.QTimer()
        self._date_list_timer.timeout.connect(self._update_date_list)
        self._date_list_timer.start(self._DATE_LIST_REFRESH_INTERVAL)

        # set window size
        screen = QDesktopWidget().screenGeometry()
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))

        # connect signals and slots
        self.experiment_list.experiment_activated.connect(self.open_plots)
        self.date_list.dates_selected.connect(self.set_date_selection)
        self.run_list.runs_selected.connect(self.set_run_selection)
        self.new_datadir_selected.connect(self.update_datadir)
        self.experiment_list.experiment_selected.connect(
            self.experiment_preview.display_datadir_path
        )
        self._today_folder_monitor.new_measurement_found.connect(
            self._on_new_measurement
        )
        self.top_bar.liveplotting_changed.connect(self._liveplotting_changed)

        # update data directory if provided
        if datadir is not None:
            self.update_datadir()

        # set content as central widget
        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.top_bar)
        layout.addWidget(splitter)
        layout.setStretchFactor(splitter, 1)
        content.setLayout(layout)

        self.setCentralWidget(content)

    @QtCore.pyqtSlot(bool)
    def _liveplotting_changed(self, liveplotting: bool) -> None:
        self._auto_open_plots = liveplotting

    @QtCore.pyqtSlot(str, str)
    def open_plots(self, tuid: str, measurement_name: str) -> None:
        device_config_path = f"{self.datadir}{tuid[:8]}/{tuid}-{measurement_name}/{measurement_name}.json"
        with open(device_config_path) as js:
            device_config = json.load(js)

        for element in device_config:
            device_config[element] = device_config[element]["data"]

        ds = safe_load_dataset(tuid)
        p = autoplot(ds, device_config)

        # Add the plot to the list of plots and show it
        self.plots.append(p)
        p.show()

    @QtCore.pyqtSlot()
    def reload_datadir(self) -> None:
        # Update the datadir label and set the datadir
        self.top_bar.update_datadir(self.datadir)
        set_datadir(self.datadir)

        self._update_date_list()
        self._today_folder_monitor.set_datadir(self.datadir)

        # Reselect the dates to update
        self.set_date_selection(self._selected_dates)

    @QtCore.pyqtSlot()
    def close_all_plots(self) -> None:
        for plot in self.plots:
            plot.close()

    @QtCore.pyqtSlot()
    def _update_date_list(self) -> None:
        dates = get_all_dates_with_measurements()
        self.date_list.update_date_list(dates)

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
        self.date_list.setCurrentItem(self.date_list.topLevelItem(0))
        self.run_list.setCurrentItem(self.run_list.topLevelItem(0))
        if (
            self.date_list.topLevelItemCount() == 0
            or self.run_list.topLevelItemCount() == 0
        ):
            QMessageBox.warning(
                self,
                "No measurements found",
                "No measurements were found in the selected data directory.\n\nEither no measurements have been taken "
                "yet or the selected directory is not a valid quantify data directory.",
            )

    @QtCore.pyqtSlot(str)
    def _on_new_measurement(self, tuid: str):
        self.set_date_selection(self._selected_dates)
        if self._auto_open_plots:
            self.open_plots(tuid)

    @QtCore.pyqtSlot(list)
    def set_date_selection(self, dates: Sequence[str]) -> None:
        """
        Set the dates in the date widget.

        Args:
            dates: Dates to set in the widget
        """

        # If there are any dates to set
        if len(dates) > 0:
            run_selection = []
            # Iterate over the dates and add all the runs for this date to be set in the run list
            for date in dates:
                run_selection += get_runs_by_date(datetime.strptime(date, "%Y-%m-%d"))
            # Update the run list widget
            self.run_list.update_run_list(run_selection)
            self._selected_dates = tuple(dates)
        # If there are no dates to set, just clear the widget
        else:
            self._selected_dates = ()
            self.run_list.clear()
            self.experiment_list.clear()

    @QtCore.pyqtSlot(list)
    def set_run_selection(self, runs: Sequence[datetime]) -> None:
        """
        Set the runs in the run widget.

        Args:
            runs: The timestamps of runs to be set in the run widget
        """

        # If there are any runs
        if len(runs) > 0:
            selection_dict = {}
            # Iterate over the dates for the run and fetch the results for the experiments on these runs
            for date in runs:
                results = get_results_by_run(date)
                selection_dict.update(
                    {tuid: dataclasses.asdict(data) for tuid, data in results.items()}
                )
            # Fill the list with experiments in the respective widget
            self.experiment_list.set_experiments(selection_dict)
            self._selected_runs = tuple(runs)
        # If there are no runs, just clear the list of experiments
        else:
            self._selected_runs = ()
            self.experiment_list.clear()


def main(
    datadir: str | Path | None = None,
    liveplotting: bool = False,
    log_level: int | str = logging.WARNING,
) -> None:
    """
    The main function for the Quantifiles application. Initializes the Qt application,
    sets the application name and icon, creates the main window with the specified data
    directory (or None if not provided), and starts the event loop.

    Parameters
    ----------
    datadir: str | Path | None, optional (default: None) Path to the data directory to open on launch. If None, the
    user will have to select a data directory manually.
    liveplotting: bool, optional (default: False) Whether to automatically open plots for new measurements.
    log_level: int | str, optional (default: logging.WARNING) The logging level to use. Can be an integer or a string.

    Returns
    -------
        None.
    """
    app = QtWidgets.QApplication([])
    app.setApplicationName("Quantifiles")
    app.setWindowIcon(load_icon("icon.png"))

    win = DataDirInspector(datadir=datadir, auto_open_plots=liveplotting)
    win.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        appinstance = QtWidgets.QApplication.instance()
        assert appinstance is not None
        appinstance.exec_()
