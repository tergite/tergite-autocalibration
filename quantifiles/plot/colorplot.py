from __future__ import annotations
from typing import List, Sequence

from PyQt5 import QtCore
import numpy as np
import pyqtgraph
import xarray as xr

from quantifiles import units
from quantifiles.plot.baseplot import BasePlot
from quantifiles.plot.utils import set_label


class ColorPlot(BasePlot):
    def __init__(
        self,
        dataset: xr.Dataset,
        x_keys: Sequence[str] | str,
        y_keys: Sequence[str] | str,
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
        super().__init__(dataset, parent=parent)

        # self.header.set_additional_info(
        #     f"{dataset[z].long_name} ({dataset[z].attrs['units']})"
        # )

        self.y_keys = [y_keys] if isinstance(y_keys, str) else y_keys
        self.x_keys = x_keys
        # self.z = z

        self.img = pyqtgraph.ImageItem()
        self.img.setColorMap(pyqtgraph.colormap.get(colormap))

        # self.colorbar = pyqtgraph.ColorBarItem(width=16, cmap=colormap)
        # self.colorbar.setLabels(
        #     right=f"{dataset[z].long_name} ({dataset[z].attrs['units']})"
        # )

        self.plot.addItem(self.img)

        # Check that necessary attributes are present in the dataset
        # assert "long_name" in dataset[x].attrs, f"{x} attribute 'long_name' not found"
        # assert "units" in dataset[x].attrs, f"{x} attribute 'units' not found"
        # assert "long_name" in dataset[y].attrs, f"{y} attribute 'long_name' not found"
        # assert "units" in dataset[y].attrs, f"{y} attribute 'units' not found"

        x_unit, self.x_scaling = units.get_si_unit_and_scaling(
            dataset[x_keys[0]].attrs["units"]
        )
        y_unit, self.y_scaling = units.get_si_unit_and_scaling(
            dataset[x_keys[1]].attrs["units"]
        )

        # Set the data
        self.set_data(dataset)

        set_label(
            self.plot, "bottom", dataset[x_keys[0]].long_name, x_unit, dataset[x_keys[0]].attrs["units"]
        )
        set_label(
            self.plot, "left", dataset[x_keys[1]].long_name, y_unit, dataset[x_keys[1]].attrs["units"]
        )

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

        # is_uniformly_spaced = dataset and dataset.attrs.get(
        #     "grid_2d_uniformly_spaced", dataset.attrs.get("2D-grid", False)
        # )

        is_uniformly_spaced = True
        if is_uniformly_spaced:
            x_data = self.x_scaling * dataset[self.x_keys[0]].values
            y_data = self.y_scaling * dataset[self.x_keys[1]].values

            real_values = dataset[self.y_keys[0]].values[:,:,0]
            imag_values = dataset[self.y_keys[0]].values[:,:,1]
            data_values = np.transpose(np.sqrt(real_values**2 + imag_values**2))
            # z_data = np.reshape(
            #     dataset[self.z].values, (len(x_data), len(y_data)), order="F"
            # )
            self.set_image(x_data, y_data, data_values)
        else:
            raise NotImplementedError(
                "Plotting of non-uniformly spaced 2D data is not yet implemented."
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
        self.img.setImage(z_data)
        self.img.setRect(
            QtCore.QRectF(
                np.min(x_data),
                np.min(y_data),
                np.max(x_data) - np.min(x_data),
                np.max(y_data) - np.min(y_data),
            )
        )
        # self.colorbar.setImageItem(self.img, insert_in=self.plot.plotItem)

        # limits = (np.nanmin(z_data), np.nanmax(z_data))
        # if limits[0] is not np.nan and limits[1] is not np.nan:
        #     self.colorbar.setLevels(limits)

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
        index_pos = self.img.getViewBox().mapFromViewToItem(
            self.img, QtCore.QPointF(x, y)
        )
        try:
            x_idx, y_idx = int(round(index_pos.x())), int(round(index_pos.y()))
            x_idx = max(0, min(x_idx, self.img.image.shape[0] - 1))
            y_idx = max(0, min(y_idx, self.img.image.shape[1] - 1))
            z_value = self.img.image[x_idx, y_idx]
        except IndexError:
            z_value = np.nan

        # x_unit = self.dataset[self.x].attrs["units"]
        # y_unit = self.dataset[self.y].attrs["units"]
        # z_unit = self.dataset[self.z].attrs["units"]

        return (
            f"\nx = {x:.4e} \ny = {y:.3e} \nz = {z_value:.3e} "
        )
