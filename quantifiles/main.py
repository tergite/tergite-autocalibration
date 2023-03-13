from __future__ import annotations

import dataclasses
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence, cast, Mapping

from PyQt5 import QtCore, QtGui, QtWidgets
from numpy import rint
from quantify_core.data.handling import set_datadir
from quantify_core.data.types import TUID

from quantifiles.data_handling import (
    DataSetReader,
    get_results_for_date,
    safe_load_dataset,
)
from quantifiles.plot_mgr import data_plotter


class DateList(QtWidgets.QListWidget):
    """Displays a list of dates for which there are runs in the database."""

    datesSelected = QtCore.pyqtSignal(list)
    fileDropped = QtCore.pyqtSignal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        # self.setAcceptDrops(True)
        # self.setDefaultDropAction(QtCore.Qt.CopyAction)

        self.setSelectionMode(QtWidgets.QListView.ExtendedSelection)
        self.itemSelectionChanged.connect(self.sendSelectedDates)

    @QtCore.pyqtSlot(list)
    def updateDates(self, dates: Sequence[str]) -> None:
        for d in dates:
            if len(self.findItems(d, QtCore.Qt.MatchExactly)) == 0:
                self.insertItem(0, d)

        i = 0
        while i < self.count():
            elem = self.item(i)
            if elem is not None and elem.text() not in dates:
                item = self.takeItem(i)
                del item
            else:
                i += 1

            if i >= self.count():
                break

        self.sortItems(QtCore.Qt.DescendingOrder)

    @QtCore.pyqtSlot()
    def sendSelectedDates(self) -> None:
        selection = [item.text() for item in self.selectedItems()]
        self.datesSelected.emit(selection)


class RunList(QtWidgets.QTreeWidget):
    cols = ["TUID", "Name", "Date", "Time", "Keywords"]

    runSelected = QtCore.pyqtSignal(str)
    runActivated = QtCore.pyqtSignal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self.setColumnCount(len(self.cols))
        self.setHeaderLabels(self.cols)

        self.itemSelectionChanged.connect(self.selectRun)
        self.itemActivated.connect(self.activateRun)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    @QtCore.pyqtSlot(QtCore.QPoint)
    def showContextMenu(self, position: QtCore.QPoint) -> None:
        model_index = self.indexAt(position)
        item = self.itemFromIndex(model_index)
        assert item is not None

        menu = QtWidgets.QMenu()

        copy_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogSaveButton)
        copy_action = menu.addAction(copy_icon, "Copy")

        action = menu.exec_(self.mapToGlobal(position))
        if action == copy_action:
            QtWidgets.QApplication.clipboard().setText(item.text(model_index.column()))

    def addRun(self, tuid: TUID, **vals: str) -> None:
        lst = [str(tuid)]
        lst.append(vals.get("name", ""))
        lst.append(vals.get("date", ""))
        lst.append(vals.get("time", ""))
        lst.append(vals.get("keywords_", ""))

        item = QtWidgets.QTreeWidgetItem(lst)
        self.addTopLevelItem(item)

    def setRuns(self, selection: Mapping[str, Mapping[str, str]]) -> None:
        self.clear()

        # disable sorting before inserting values to avoid performance hit
        self.setSortingEnabled(False)

        for tuid, record in selection.items():
            self.addRun(tuid, **record)

        self.setSortingEnabled(True)

        for i in range(len(self.cols)):
            self.resizeColumnToContents(i)

    def updateRuns(self, selection: Mapping[int, Mapping[str, str]]) -> None:
        run_added = False
        for runId, record in selection.items():
            item = self.findItems(str(runId), QtCore.Qt.MatchExactly)
            if len(item) == 0:
                self.setSortingEnabled(False)
                self.addRun(runId, **record)
                run_added = True
            elif len(item) == 1:
                completed = (
                    record.get("completed_date", "")
                    + " "
                    + record.get("completed_time", "")
                )
                if completed != item[0].text(6):
                    item[0].setText(6, completed)

                num_records = str(record.get("records", ""))
                if num_records != item[0].text(7):
                    item[0].setText(7, num_records)
            else:
                raise RuntimeError(f"More than one runs found with runId: " f"{runId}")

        if run_added:
            self.setSortingEnabled(True)
            for i in range(len(self.cols)):
                self.resizeColumnToContents(i)

    @QtCore.pyqtSlot()
    def selectRun(self) -> None:
        selection = self.selectedItems()
        if len(selection) == 0:
            return

        tuid = selection[0].text(0)
        self.runSelected.emit(tuid)

    @QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem, int)
    def activateRun(self, item: QtWidgets.QTreeWidgetItem, _: int) -> None:
        tuid = item.text(0)
        self.runActivated.emit(tuid)


class DataDirLabel(QtWidgets.QLabel):
    def __init__(self, datadir: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self.updateDataDir(datadir)

    def updateDataDir(self, datadir: str) -> None:
        if datadir is None:
            self.setText("No data directory selected")
        else:
            self.setText(f"Data directory: {datadir}")


class DataDirInspector(QtWidgets.QMainWindow):
    _WINDOW_TITLE: str = "Quantifiles | Quantify dataset browser"
    _WINDOW_SIZE: int = 640

    datadirSelected = QtCore.pyqtSignal(str)

    def __init__(
        self, datadir: str | None = None, parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)

        self.datadir = datadir
        self._selected_dates: tuple[str, ...] = ()
        self.plots = []

        self.setWindowTitle(self._WINDOW_TITLE)

        # ---- widgets ----
        self.dateList = DateList()
        self.runList = RunList()

        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.dateList)
        splitter.addWidget(self.runList)
        splitter.setSizes([100, 800])

        self.setCentralWidget(splitter)

        # ---- end widgets ----

        self._datadir_label = DataDirLabel(datadir)

        self.toolbar = self.addToolBar("Datadir toolbar")
        self.toolbar.addWidget(self._datadir_label)
        self.toolbar.setMovable(False)

        # self.toolbar.addSeparator()

        # ---- menu bar ----
        menu = self.menuBar()
        fileMenu = menu.addMenu("&File")

        # action: load db file
        loadAction = QtWidgets.QAction("&Open", self)
        loadAction.setShortcut("Ctrl+O")
        loadAction.triggered.connect(self.configure_datadir)
        fileMenu.addAction(loadAction)

        # action: updates from the db file
        refreshAction = QtWidgets.QAction("&Reload", self)
        refreshAction.setShortcut("Ctrl+R")
        # refreshAction.triggered.connect(self.refreshDB)
        fileMenu.addAction(refreshAction)

        # ---- end menu bar ----

        # sizing
        scaledSize = int(self._WINDOW_SIZE * rint(self.logicalDpiX() / 96.0))
        self.resize(2 * scaledSize, scaledSize)

        # signals
        self.runList.runActivated.connect(self.open_plots)
        self.dateList.datesSelected.connect(self.setDateSelection)
        self.datadirSelected.connect(self.update_datadir)

        # set the datadir
        if datadir is not None:
            self.update_datadir()

    @QtCore.pyqtSlot(str)
    def open_plots(self, tuid: str) -> None:
        ds = safe_load_dataset(tuid)
        p = data_plotter(ds)
        self.plots.append(p)

    @QtCore.pyqtSlot()
    def configure_datadir(self) -> None:
        curdir = self.datadir if self.datadir is not None else os.getcwd()

        path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Open quantify datadirectory",
            curdir,
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if path:
            self.datadir = path
            self.datadirSelected.emit(path)

    def update_datadir(self) -> None:
        self._datadir_label.updateDataDir(self.datadir)
        set_datadir(self.datadir)

        dates = DataSetReader.get_all_dates_with_measurements()
        self.dateList.updateDates([date.strftime("%Y-%m-%d") for date in dates])
        self.dateList.setCurrentRow(0)

    @QtCore.pyqtSlot(list)
    def setDateSelection(self, dates: Sequence[str]) -> None:
        if len(dates) > 0:
            selection_dict = {}
            for date in dates:
                results = get_results_for_date(datetime.strptime(date, "%Y-%m-%d"))
                selection_dict.update(
                    {tuid: dataclasses.asdict(data) for tuid, data in results.items()}
                )

            self.runList.setRuns(selection_dict)
            self._selected_dates = tuple(dates)
        else:
            self._selected_dates = ()
            self.runList.clear()


def main(
    datadir: str | Path | None = None, log_level: int | str = logging.WARNING
) -> None:
    app = QtWidgets.QApplication([])

    win = DataDirInspector(datadir=datadir)
    win.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        appinstance = QtWidgets.QApplication.instance()
        assert appinstance is not None
        appinstance.exec_()


if __name__ == "__main__":
    qf = main(r"C:\Users\Damie\PycharmProjects\quantifiles\test_data")
