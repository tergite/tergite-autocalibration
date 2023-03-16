from __future__ import annotations

import xarray as xr

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QSignalMapper


class SingleGettableBox(QtWidgets.QFrame):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        gettable_name: str = "",
        dataset: xr.Dataset | None = None,
    ):
        super().__init__(parent)
        gettable_long_name = dataset[gettable_name].long_name
        box_title = f"{gettable_name} ({gettable_long_name})"

        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)

        grid_layout = QtWidgets.QGridLayout(self)
        param_table_layout = QtWidgets.QGridLayout(self)

        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setChecked(True)

        label = QtWidgets.QLabel(box_title)
        underline = QtWidgets.QFrame()
        underline.setFrameShape(QtWidgets.QFrame.HLine)
        underline.setFrameShadow(QtWidgets.QFrame.Sunken)

        grid_layout.addWidget(self.checkbox, 0, 0)
        grid_layout.addWidget(label, 0, 1)
        grid_layout.addWidget(underline, 1, 1)

        grid_layout.addLayout(param_table_layout, 2, 1)

        for idx, settable_name in enumerate(dataset[gettable_name].coords.keys()):
            settable_long_name = dataset[gettable_name][settable_name].long_name

            label_short_name = QtWidgets.QLabel(str(settable_name))
            label_long_name = QtWidgets.QLabel(str(settable_long_name))
            label_settable_unit = QtWidgets.QLabel(str(dataset[gettable_name][settable_name].attrs["units"]))

            param_table_layout.addWidget(label_short_name, idx, 0)
            param_table_layout.addWidget(label_long_name, idx, 1)
            param_table_layout.addWidget(label_settable_unit, idx, 2)

        label_short_name = QtWidgets.QLabel(str(gettable_name))
        label_long_name = QtWidgets.QLabel(str(gettable_long_name))
        label_settable_unit = QtWidgets.QLabel(str(dataset[gettable_name].attrs["units"]))
        number_of_settables = len(dataset[gettable_name].coords.keys())

        param_table_layout.addWidget(label_short_name, number_of_settables + 1, 0)
        param_table_layout.addWidget(label_long_name, number_of_settables + 1, 1)
        param_table_layout.addWidget(label_settable_unit, number_of_settables + 1, 2)

        self.setLayout(grid_layout)


class GettableSelectBox(QtWidgets.QFrame):

    gettable_toggled = QtCore.pyqtSignal(str, bool)

    def __init__(
        self, parent: QtWidgets.QWidget | None = None, dataset: xr.Dataset | None = None
    ):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel("Dataset contents:")
        spacer = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        layout.addSpacerItem(spacer)
        layout.addWidget(label)

        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setLayout(layout)

        self.gettable_select_mapper = QSignalMapper()
        self.gettable_select_mapper.mapped[str].connect(self.gettable_state_changed)

        self._gettable_checkboxes = {}
        for idx, gettable_name in enumerate(dataset.data_vars.keys()):
            gettable_box = SingleGettableBox(gettable_name=gettable_name, dataset=dataset)
            gettable_box.checkbox.stateChanged.connect(
                self.gettable_select_mapper.map
            )
            self.gettable_select_mapper.setMapping(
                gettable_box.checkbox, gettable_name
            )
            self._gettable_checkboxes[gettable_name] = gettable_box.checkbox

            layout.addWidget(
                gettable_box,
            )
        layout.addSpacerItem(spacer)

    def gettable_state_changed(self, name: str):
        enabled = self._gettable_checkboxes[name].isChecked()
        self.gettable_toggled.emit(name, enabled)


class PlotWindowContent(QtWidgets.QWidget):
    def __init__(
        self, parent: QtWidgets.QWidget | None = None, dataset: xr.Dataset | None = None
    ):
        super().__init__(parent)
        self.gettable_select_box = GettableSelectBox(dataset=dataset)
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.gettable_select_box)
        self.setLayout(layout)


class PlotWindow(QtWidgets.QMainWindow):
    _WINDOW_TITLE: str = "Quantifiles plot window"
    _WINDOW_SIZE: int = 200

    def __init__(self, dataset: xr.Dataset, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.dataset = dataset
        self.plots = {}

        tuid = self.dataset.tuid if hasattr(self.dataset, "tuid") else "no tuid"
        self.setWindowTitle(f"{self._WINDOW_TITLE} | {tuid}")

        canvas = PlotWindowContent(self, dataset=dataset)
        self.canvas = canvas
        self.setCentralWidget(canvas)

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setMinimumSize(self._WINDOW_SIZE, self._WINDOW_SIZE)

        canvas.gettable_select_box.gettable_toggled.connect(self.toggle_gettable)

    def add_plot(self, name: str, plot: QtWidgets.QWidget):
        self.canvas.layout().addWidget(plot)
        self.plots[name] = plot

    @QtCore.pyqtSlot(str, bool)
    def toggle_gettable(self, name: str, enabled: bool):
        self.plots[name].setVisible(enabled)
