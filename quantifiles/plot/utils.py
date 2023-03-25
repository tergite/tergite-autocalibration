from __future__ import annotations

from pathlib import Path

import xarray as xr
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from pyqtgraph.widgets import PlotWidget
from quantify_core.data.handling import locate_experiment_container, DATASET_NAME
from quantify_core.data.types import TUID

from quantifiles.watcher import FileMonitor


def set_label(
    plot: PlotWidget, axis: str, name: str, unit: str | None, default_unit: str
):
    """
    Set the label of the specified axis on the given plot widget.

    Parameters
    ----------
    plot : PlotWidget
        The plot widget to set the label on.
    axis : str
        The axis to set the label for ('left', 'bottom', 'right', or 'top').
    name : str
        The name of the label to set.
    unit : str, optional
        The units of the label (e.g. 'm', 's', 'kg'). If `None`, the `default_unit` will be used and pyqtgraph will not
        rescale the axis. We assume that this is always an SI unit.
    default_unit : str
        The default units to use if `unit` is `None`.

    Returns
    -------
    None
    """
    label = f"{name} ({default_unit})" if unit is None else name
    plot.setLabel(
        axis,
        label,
        units=unit,
    )


def copy_to_clipboard(widget: QtWidgets.QWidget) -> None:
    """
    Copy the given widget to the clipboard as an image.

    Parameters
    ----------
    widget:
        The widget to copy to the clipboard.

    Returns
    -------
    None
    """
    QApplication.clipboard().setImage(widget.grab().toImage())


def get_file_monitor_for_dataset(dataset: xr.Dataset) -> FileMonitor:
    """
    Get a FileMonitor for a dataset.

    Parameters
    ----------
    dataset : DataSet
        The dataset to get a FileMonitor for.

    Returns
    -------
    FileMonitor
        The FileMonitor for the dataset.
    """
    tuid = TUID(dataset.attrs["tuid"])
    directory = Path(locate_experiment_container(tuid))
    monitor = FileMonitor(directory / DATASET_NAME)
    return monitor
