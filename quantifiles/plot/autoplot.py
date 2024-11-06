from typing import cast

from PyQt5 import QtWidgets
from quantify_core.data.handling import set_datadir
import xarray as xr

from quantifiles.data import safe_load_dataset
from quantifiles.plot.colorplot import ColorPlot
from quantifiles.plot.lineplot import LinePlot
from quantifiles.plot.loki_window import PlotWindow
from quantifiles.plot.multiple_line_plot import MultipleLinePlot


# rename it to initial_plot
def autoplot(dataset: xr.Dataset, device_config: dict) -> QtWidgets.QMainWindow:
    plot_window = PlotWindow(dataset, device_config)

    for var in dataset.data_vars:
        qubit = dataset[var].attrs["qubit"]
        gettable = cast(str, var)
        settables = list(dataset[var].coords.keys())

        if len(settables) == 1:
            settable = cast(str, settables[0])
            plot_widget = LinePlot(
                dataset, x_key=settable, y_keys=gettable, parent=plot_window
            )
        elif len(settables) == 2:
            settables = [cast(str, settable) for settable in settables]
            plot_widget = ColorPlot(
                dataset, x_keys=settables, y_keys=gettable, parent=plot_window
            )
            secondary_plot_widget = MultipleLinePlot(
                dataset, x_keys=settables, y_keys=gettable, parent=plot_window
            )
        else:
            raise ValueError("Cant plot datasets with more than 2 settables :(")
        plot_window.add_plot(qubit, plot_widget)
        if len(settables) == 2:
            plot_window.add_plot(qubit, plot_widget, secondary_plot_widget)
        else:
            plot_window.add_plot(qubit, plot_widget)

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
