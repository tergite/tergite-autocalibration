from __future__ import annotations
from itertools import cycle
from typing import List, Sequence

from PyQt5 import QtCore
import numpy as np
import pyqtgraph
import xarray as xr

from quantifiles import units
from quantifiles.plot.baseplot import BasePlot
from quantifiles.plot.lineplot import _OPTIONS
from quantifiles.plot.utils import set_label


class MultipleLinePlot(BasePlot):
    def __init__(
        self,
        dataset: xr.Dataset,
        x_keys: Sequence[str] | str,
        y_keys: Sequence[str] | str,
        colormap: str = "viridis",
        parent=None,
    ):
        """
        Create a collection of the line plots that consist a 2D color plot of the given dataset.

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
        # self.img = pyqtgraph.ImageItem()
        # self.img.setColorMap(pyqtgraph.colormap.get(colormap))

        # self.colorbar = pyqtgraph.ColorBarItem(width=16, cmap=colormap)
        # self.colorbar.setLabels(
        #     right=f"{dataset[z].long_name} ({dataset[z].attrs['units']})"
        # )

        # self.plot.addItem(self.img)
        self.curves = self.create_curves(dataset)

        x_unit, self.x_scaling = units.get_si_unit_and_scaling(
            dataset[x_keys[0]].attrs["units"]
        )
        y_unit, self.y_scaling = units.get_si_unit_and_scaling(
            dataset[x_keys[1]].attrs["units"]
        )

        # Set the data
        self.set_data(dataset)

        set_label(
            self.plot,
            "bottom",
            dataset[x_keys[0]].long_name,
            x_unit,
            dataset[x_keys[0]].attrs["units"],
        )
        set_label(
            self.plot,
            "left",
            dataset[x_keys[1]].long_name,
            y_unit,
            dataset[x_keys[1]].attrs["units"],
        )

    def create_curves(self, dataset: xr.Dataset):
        options_generator = cycle(_OPTIONS)

        inner_settable = self.x_keys[0]
        outer_settable = self.x_keys[1]

        x_data = dataset[inner_settable].values
        curves = []

        for outer_index, outer_value in enumerate(dataset[outer_settable].values):
            real_values = (
                dataset[self.y_keys[0]].isel({outer_settable: outer_index})[:, 0].values
            )
            imag_values = (
                dataset[self.y_keys[0]].isel({outer_settable: outer_index})[:, 1].values
            )
            magnitudes = np.sqrt(real_values**2 + imag_values**2)

            curve = self.plot.plot(
                x_data,
                magnitudes,
                **next(options_generator),
                # name=curve_name,
                connect="finite",
            )
            curves.append(curve)
        return curves

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
        text = (
            f"\nx = {x:.3e} {self.dataset[self.x_keys[0]].attrs['units']} "
            f"\ny = {y:.3e} {self.dataset[self.y_keys[0]].attrs['units']}"
        )
        return text
