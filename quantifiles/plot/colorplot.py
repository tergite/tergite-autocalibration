from PyQt5 import QtWidgets, QtCore
import pyqtgraph

import numpy as np
import xarray as xr

from quantifiles import units
from quantifiles.plot.utils import set_label

COLORMAP = "viridis"


class ColorPlot(QtWidgets.QFrame):
    def __init__(self, dataset: xr.Dataset, x: str, y: str, z: str, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)
        self.setStyleSheet("background-color:white;")

        self.dataset = dataset
        self.x = x
        self.y = y
        self.z = z

        pyqtgraph.setConfigOption("background", None)
        pyqtgraph.setConfigOption("foreground", "k")

        self.img = pyqtgraph.ImageItem()
        self.plot = pyqtgraph.PlotWidget()
        self.img.setColorMap(pyqtgraph.colormap.get(COLORMAP))
        self.colorbar = pyqtgraph.ColorBarItem()

        x_unit, x_scaling = units.get_si_unit_and_scaling(dataset[x].attrs["units"])
        y_unit, y_scaling = units.get_si_unit_and_scaling(dataset[y].attrs["units"])

        is_uniformly_spaced = dataset and dataset.attrs.get(
            "grid_2d_uniformly_spaced", dataset.attrs.get("2D-grid", False)
        )
        if is_uniformly_spaced:
            x_data = x_scaling * dataset[x].values[: dataset.attrs["xlen"]]
            y_data = y_scaling * dataset[y].values[:: dataset.attrs["xlen"]]
            z_data = np.reshape(
                dataset[z].values, (len(x_data), len(y_data)), order="F"
            )
            self.set_image(x_data, y_data, z_data)
        else:
            raise NotImplementedError(
                "Plotting of non-uniformly spaced 2D data is not yet implemented."
            )
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.plot)
        set_label(
            self.plot, "bottom", dataset[x].long_name, x_unit, dataset[x].attrs["units"]
        )
        set_label(
            self.plot, "left", dataset[y].long_name, y_unit, dataset[y].attrs["units"]
        )

    def set_image(self, x_data: np.ndarray, y_data: np.ndarray, z_data: np.ndarray):
        self.plot.addItem(self.img)
        self.img.setImage(z_data)
        self.img.setRect(
            QtCore.QRectF(
                np.min(x_data),
                np.min(y_data),
                np.max(x_data) - np.min(x_data),
                np.max(y_data) - np.min(y_data),
            )
        )
