from __future__ import annotations

import xarray as xr

from PyQt5 import QtWidgets, QtCore

from quantify_core.data.handling import set_datadir

from quantifiles.data import safe_load_dataset
from quantifiles.plot.colorplot import ColorPlot
from quantifiles.plot.lineplot import LinePlot


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

        checkbox = QtWidgets.QCheckBox()
        checkbox.setChecked(True)

        label = QtWidgets.QLabel(box_title)
        underline = QtWidgets.QFrame()
        underline.setFrameShape(QtWidgets.QFrame.HLine)
        underline.setFrameShadow(QtWidgets.QFrame.Sunken)

        grid_layout.addWidget(checkbox, 0, 0)
        grid_layout.addWidget(label, 0, 1)
        grid_layout.addWidget(underline, 1, 1)

        grid_layout.addLayout(param_table_layout, 2, 1)

        for idx, settable_name in enumerate(dataset[gettable_name].coords.keys()):
            settable_long_name = dataset[gettable_name][settable_name].long_name

            label_short_name = QtWidgets.QLabel(str(settable_name))
            label_long_name = QtWidgets.QLabel(str(settable_long_name))
            param_table_layout.addWidget(label_short_name, idx, 0)
            param_table_layout.addWidget(label_long_name, idx, 1)

        label_short_name = QtWidgets.QLabel(str(gettable_name))
        label_long_name = QtWidgets.QLabel(str(gettable_long_name))
        number_of_settables = len(dataset[gettable_name].coords.keys())
        param_table_layout.addWidget(label_short_name, number_of_settables + 1, 0)
        param_table_layout.addWidget(label_long_name, number_of_settables + 1, 1)

        self.setLayout(grid_layout)


class GettableSelectBox(QtWidgets.QFrame):
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

        for gettable_name in dataset.data_vars.keys():
            layout.addWidget(
                SingleGettableBox(gettable_name=gettable_name, dataset=dataset)
            )
        layout.addSpacerItem(spacer)


class PlotWindowContent(QtWidgets.QWidget):
    def __init__(
        self, parent: QtWidgets.QWidget | None = None, dataset: xr.Dataset | None = None
    ):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(GettableSelectBox(self, dataset=dataset))
        self.setLayout(layout)


class PlotWindow(QtWidgets.QMainWindow):
    _WINDOW_TITLE: str = "Quantifiles plot window"
    _WINDOW_SIZE: int = 200

    def __init__(self, dataset: xr.Dataset, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.dataset = dataset

        tuid = self.dataset.tuid if hasattr(self.dataset, "tuid") else "no tuid"
        self.setWindowTitle(f"{self._WINDOW_TITLE} | {tuid}")

        canvas = PlotWindowContent(self, dataset=dataset)
        self.canvas = canvas
        self.setCentralWidget(canvas)

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setMinimumSize(self._WINDOW_SIZE, self._WINDOW_SIZE)

    def add_plot(self, plot: QtWidgets.QWidget):
        self.canvas.layout().addWidget(plot)
