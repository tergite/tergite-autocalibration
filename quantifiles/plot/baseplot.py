from abc import abstractmethod
from functools import partial

import xarray as xr

import pyqtgraph
from pyqtgraph.Qt import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from quantifiles.data import safe_load_dataset
from quantifiles.plot.header import PlotHeader
from quantifiles.plot.utils import get_file_monitor_for_dataset, copy_to_clipboard


class BasePlot(QtWidgets.QFrame):
    mouse_text_changed = pyqtSignal(str)

    def __init__(self, dataset: xr.Dataset, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)
        self.setStyleSheet("background-color:white;")

        self.dataset = dataset

        pyqtgraph.setConfigOption("background", None)
        pyqtgraph.setConfigOption("foreground", "k")

        self._file_monitor = get_file_monitor_for_dataset(self.dataset)
        self._file_monitor.file_modified.connect(self._reload_data)
        self._file_monitor.start()

        self.header = PlotHeader(
            name=dataset.name,
            tuid=dataset.tuid,
            additional_info="",
            parent=self,
        )
        self.plot = pyqtgraph.PlotWidget()

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.header)
        self.layout().addWidget(self.plot)

        # Create a 'Copy to Clipboard' QAction and add it to the plot's context menu
        self.copy_action = QtGui.QAction(
            "Copy to Clipboard", self.plot.plotItem.vb.menu
        )
        self.copy_action.triggered.connect(partial(copy_to_clipboard, self))
        self.plot.plotItem.vb.menu.addSeparator()
        self.plot.plotItem.vb.menu.addAction(self.copy_action)

        self.proxy = pyqtgraph.SignalProxy(
            self.plot.scene().sigMouseMoved, rateLimit=30, slot=self.mouse_moved
        )

    @pyqtSlot(tuple)
    def mouse_moved(self, pos):
        """
        Callback for when the mouse is moved over the plot.

        Parameters
        ----------
        pos: tuple
            The position of the mouse in the plot.

        Returns
        -------
        None
        """
        if self.plot.sceneBoundingRect().contains(*pos):
            mouse_point = self.plot.plotItem.vb.mapSceneToView(*pos)
            self.mouse_text_changed.emit(
                self.get_mouse_position_text(mouse_point.x(), mouse_point.y())
            )

    @abstractmethod
    def get_mouse_position_text(self, x: float, y: float) -> str:
        """
        Get the text to display when the mouse is moved over the plot.

        Parameters
        ----------
        x: float
            The x-coordinate of the mouse.
        y: float
            The y-coordinate of the mouse.

        Returns
        -------
        str
            The text to display.
        """

    @pyqtSlot()
    def _reload_data(self) -> None:
        """
        Callback for when the file is modified.

        Returns
        -------
        None
        """
        self.set_data(safe_load_dataset(self.dataset.tuid))

    @abstractmethod
    def set_data(self, dataset: xr.Dataset) -> None:
        """
        Set the data to be displayed in the plot.

        Parameters
        ----------
        dataset: xr.Dataset
            The dataset to plot.

        Returns
        -------
        None
        """
