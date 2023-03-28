from typing import cast

import xarray as xr
from PyQt5 import QtWidgets
from quantify_core.data.handling import set_datadir

from quantifiles.data import safe_load_dataset
from quantifiles.plot.colorplot import ColorPlot
from quantifiles.plot.lineplot import LinePlot
from quantifiles.plot.window import PlotWindow


def autoplot(dataset: xr.Dataset) -> QtWidgets.QMainWindow:
    plot_window = PlotWindow(dataset)

    gettables = [k for k in dataset.keys() if k.startswith("y")]
    settables = [k for k in dataset.variables.keys() if k.startswith("x")]
    num_settables = len(settables)
    for gettable in gettables:
        gettable = cast(str, gettable)
        if num_settables == 2 and dataset.attrs.get(
            "grid_2d_uniformly_spaced", dataset.attrs.get("2D-grid", False)
        ):
            plot_widget = ColorPlot(
                dataset, x="x0", y="x1", z=gettable, parent=plot_window
            )
            plot_window.add_plot(gettable, plot_widget)
        else:
            for settable in settables:
                settable = cast(str, settable)
                plot_widget = LinePlot(
                    dataset, x_key=settable, y_keys=gettable, parent=plot_window
                )
                plot_window.add_plot(gettable, plot_widget)

    return plot_window


if __name__ == "__main__":
    set_datadir(r"C:\Users\Damie\PycharmProjects\quantifiles\test_data")

    dataset = safe_load_dataset("20230312-182213-487-38d5f1")
    # dataset = safe_load_dataset("20200504-191556-002-4209ee")
    # dataset = safe_load_dataset("20220930-104712-924-d6f761")

    app = QtWidgets.QApplication([])
    window = autoplot(dataset)
    window.show()
    app.exec_()
