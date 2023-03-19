from __future__ import annotations

from functools import partial
from itertools import cycle
from typing import Sequence

from PyQt5 import QtWidgets
import pyqtgraph

import xarray as xr
from pyqtgraph.Qt import QtGui

from quantifiles.plot import utils
from quantifiles.plot.utils import copy_to_clipboard
from quantifiles.units import get_si_unit_and_scaling

_OPTIONS = [
    {
        "pen": (0, 114, 189),
        "symbolBrush": (0, 114, 189),
        "symbolPen": "w",
        "symbol": "p",
        "symbolSize": 12,
    },
    {
        "pen": (217, 83, 25),
        "symbolBrush": (217, 83, 25),
        "symbolPen": "w",
        "symbol": "h",
        "symbolSize": 12,
    },
    {
        "pen": (250, 194, 5),
        "symbolBrush": (250, 194, 5),
        "symbolPen": "w",
        "symbol": "t3",
        "symbolSize": 12,
    },
    {
        "pen": (54, 55, 55),
        "symbolBrush": (55, 55, 55),
        "symbolPen": "w",
        "symbol": "s",
        "symbolSize": 12,
    },
    {
        "pen": (119, 172, 48),
        "symbolBrush": (119, 172, 48),
        "symbolPen": "w",
        "symbol": "d",
        "symbolSize": 12,
    },
    {
        "pen": (19, 234, 201),
        "symbolBrush": (19, 234, 201),
        "symbolPen": "w",
        "symbol": "t1",
        "symbolSize": 12,
    },
    {
        "pen": (0, 0, 200),
        "symbolBrush": (0, 0, 200),
        "symbolPen": "w",
        "symbol": "o",
        "symbolSize": 12,
    },
    {
        "pen": (0, 128, 0),
        "symbolBrush": (0, 128, 0),
        "symbolPen": "w",
        "symbol": "t",
        "symbolSize": 12,
    },
    {
        "pen": (195, 46, 212),
        "symbolBrush": (195, 46, 212),
        "symbolPen": "w",
        "symbol": "t2",
        "symbolSize": 12,
    },
    {
        "pen": (237, 177, 32),
        "symbolBrush": (237, 177, 32),
        "symbolPen": "w",
        "symbol": "star",
        "symbolSize": 12,
    },
    {
        "pen": (126, 47, 142),
        "symbolBrush": (126, 47, 142),
        "symbolPen": "w",
        "symbol": "+",
        "symbolSize": 12,
    },
]


class LinePlot(QtWidgets.QFrame):
    def __init__(
        self,
        dataset: xr.Dataset,
        x_key: str,
        y_keys: Sequence[str] | str,
        parent=None,
    ):
        super().__init__(parent)
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)
        self.setStyleSheet("background-color:white;")

        self.y_keys = [y_keys] if isinstance(y_keys, str) else y_keys
        self.x_key = x_key

        self.parent = parent
        self.dataset = dataset

        pyqtgraph.setConfigOption("background", None)
        pyqtgraph.setConfigOption("foreground", "k")

        layout = QtWidgets.QVBoxLayout()

        self.plot = pyqtgraph.PlotWidget()
        self.plot.addLegend()
        self.curves = self.create_curves()

        # Create a 'Copy to Clipboard' QAction and add it to the plot's context menu
        self.copy_action = QtGui.QAction(
            "Copy to Clipboard", self.plot.plotItem.vb.menu
        )
        self.copy_action.triggered.connect(partial(copy_to_clipboard, self))
        self.plot.plotItem.vb.menu.addSeparator()
        self.plot.plotItem.vb.menu.addAction(self.copy_action)

        x_unit, x_scaling = get_si_unit_and_scaling(self.dataset[x_key].attrs["units"])
        y_unit, y_scaling = get_si_unit_and_scaling(
            self.dataset[self.y_keys[0]].attrs["units"]
        )

        utils.set_label(
            self.plot,
            "bottom",
            self.dataset[x_key].long_name,
            x_unit,
            self.dataset[x_key].attrs["units"],
        )
        utils.set_label(
            self.plot,
            "left",
            self.dataset[self.y_keys[0]].long_name,
            y_unit,
            self.dataset[self.y_keys[0]].attrs["units"],
        )

        self.plot.showGrid(x=True, y=True)
        if all([self.dataset[key].attrs["units"] == "%" for key in self.y_keys]):
            self.plot.setYRange(0, 1)

        layout.addWidget(self.plot)
        self.setLayout(layout)

    def create_curves(self, x_scaling: float = 1, y_scaling: float = 1):
        options_generator = cycle(_OPTIONS)
        curves = []
        for y_var in self.y_keys:
            curve_name = f"{self.dataset[y_var].name}: {self.dataset[y_var].long_name}"
            curve = self.plot.plot(
                x_scaling * self.dataset[self.x_key].values,
                y_scaling * self.dataset[y_var].values,
                **next(options_generator),
                name=curve_name,
                connect="finite",
            )
            curves.append(curve)
        return curves
