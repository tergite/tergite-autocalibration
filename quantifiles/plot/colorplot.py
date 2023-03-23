from functools import partial

from PyQt5 import QtWidgets, QtCore
import pyqtgraph

import numpy as np
import xarray as xr
from PyQt5.QtWidgets import QApplication
from pyqtgraph.Qt import QtGui

from quantifiles import units
from quantifiles.plot.header import PlotHeader
from quantifiles.plot.utils import set_label, copy_to_clipboard


class ColorPlot(QtWidgets.QFrame):
    def __init__(
        self,
        dataset: xr.Dataset,
        x: str,
        y: str,
        z: str,
        colormap: str = "viridis",
        parent=None,
    ):
        """
        Create a 2D color plot of the given dataset.

        Parameters
        ----------
        dataset: xr.Dataset
            The dataset to plot.
        x: str
            The name of the x-axis variable.
        y: str
            The name of the y-axis variable.
        z: str
            The name of the z-axis variable.
        colormap: str, optional
            The name of the colormap to use. By default, 'viridis' is used.
        parent: QtWidgets.QWidget, optional
            The parent widget of this widget. By default, `None`.
        """
        super().__init__(parent)
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)
        self.setStyleSheet("background-color:white;")

        self.dataset = dataset
        self.x = x
        self.y = y
        self.z = z

        pyqtgraph.setConfigOption("background", None)
        pyqtgraph.setConfigOption("foreground", "k")

        # Create the widgets
        self.img = pyqtgraph.ImageItem()
        self.plot = pyqtgraph.PlotWidget()
        self.img.setColorMap(pyqtgraph.colormap.get(colormap))
        self.colorbar = pyqtgraph.ColorBarItem()
        self.header = PlotHeader(
            name=dataset.name,
            tuid=dataset.tuid,
            additional_info=f"{dataset[z].long_name} ({dataset[z].attrs['units']})",
            parent=self,
        )

        # Create a 'Copy to Clipboard' QAction and add it to the plot's context menu
        self.copy_action = QtGui.QAction(
            "Copy to Clipboard", self.plot.plotItem.vb.menu
        )
        self.copy_action.triggered.connect(partial(copy_to_clipboard, self))
        self.plot.plotItem.vb.menu.addSeparator()
        self.plot.plotItem.vb.menu.addAction(self.copy_action)

        # Check that necessary attributes are present in the dataset
        assert "long_name" in dataset[x].attrs, f"{x} attribute 'long_name' not found"
        assert "units" in dataset[x].attrs, f"{x} attribute 'units' not found"
        assert "long_name" in dataset[y].attrs, f"{y} attribute 'long_name' not found"
        assert "units" in dataset[y].attrs, f"{y} attribute 'units' not found"

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
        self.layout().addWidget(self.header)
        self.layout().addWidget(self.plot)
        set_label(
            self.plot, "bottom", dataset[x].long_name, x_unit, dataset[x].attrs["units"]
        )
        set_label(
            self.plot, "left", dataset[y].long_name, y_unit, dataset[y].attrs["units"]
        )

    def set_image(
        self, x_data: np.ndarray, y_data: np.ndarray, z_data: np.ndarray
    ) -> None:
        """
        Set the image to be displayed in the plot.

        Parameters
        ----------
        x_data: np.ndarray
            The x-axis data. Must be 1D.
        y_data: np.ndarray
            The y-axis data. Must be 1D.
        z_data: np.ndarray
            The z-axis data. Must be 1D.

        Returns
        -------
        None
        """
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
