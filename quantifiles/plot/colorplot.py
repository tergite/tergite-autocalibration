from PyQt5 import QtWidgets, QtCore
import pyqtgraph

import numpy as np
import xarray as xr

COLORMAP = "viridis"


class ColorPlot(QtWidgets.QWidget):
    def __init__(self, dataset: xr.Dataset, x: str, y: str, z: str, parent=None):
        super().__init__(parent)

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

        is_uniformly_spaced = dataset and dataset.attrs.get(
            "grid_2d_uniformly_spaced", dataset.attrs.get("2D-grid", False)
        )
        if is_uniformly_spaced:
            x_data = dataset[x].values[: dataset.attrs["xlen"]]
            y_data = dataset[y].values[:: dataset.attrs["xlen"]]
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

        self.plot.setLabel(
            "left",
            self.dataset[y].long_name,
            units=self.dataset[y].attrs["units"],
        )
        self.plot.setLabel(
            "bottom",
            self.dataset[x].long_name,
            units=self.dataset[x].attrs["units"],
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
