from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg

from quantifiles.plots.unit_management import (
    return_unit_scaler,
    format_unit,
    format_value_and_unit,
)

graph_color = []
graph_color += [
    {
        "pen": (0, 114, 189),
        "symbolBrush": (0, 114, 189),
        "symbolPen": "w",
        "symbol": "p",
        "symbolSize": 12,
    }
]
graph_color += [
    {
        "pen": (217, 83, 25),
        "symbolBrush": (217, 83, 25),
        "symbolPen": "w",
        "symbol": "h",
        "symbolSize": 12,
    }
]
graph_color += [
    {
        "pen": (250, 194, 5),
        "symbolBrush": (250, 194, 5),
        "symbolPen": "w",
        "symbol": "t3",
        "symbolSize": 12,
    }
]
graph_color += [
    {
        "pen": (54, 55, 55),
        "symbolBrush": (55, 55, 55),
        "symbolPen": "w",
        "symbol": "s",
        "symbolSize": 12,
    }
]
graph_color += [
    {
        "pen": (119, 172, 48),
        "symbolBrush": (119, 172, 48),
        "symbolPen": "w",
        "symbol": "d",
        "symbolSize": 12,
    }
]
graph_color += [
    {
        "pen": (19, 234, 201),
        "symbolBrush": (19, 234, 201),
        "symbolPen": "w",
        "symbol": "t1",
        "symbolSize": 12,
    }
]
graph_color += [
    {
        "pen": (0, 0, 200),
        "symbolBrush": (0, 0, 200),
        "symbolPen": "w",
        "symbol": "o",
        "symbolSize": 12,
    }
]
graph_color += [
    {
        "pen": (0, 128, 0),
        "symbolBrush": (0, 128, 0),
        "symbolPen": "w",
        "symbol": "t",
        "symbolSize": 12,
    }
]
graph_color += [
    {
        "pen": (195, 46, 212),
        "symbolBrush": (195, 46, 212),
        "symbolPen": "w",
        "symbol": "t2",
        "symbolSize": 12,
    }
]
graph_color += [
    {
        "pen": (237, 177, 32),
        "symbolBrush": (237, 177, 32),
        "symbolPen": "w",
        "symbol": "star",
        "symbolSize": 12,
    }
]
graph_color += [
    {
        "pen": (126, 47, 142),
        "symbolBrush": (126, 47, 142),
        "symbolPen": "w",
        "symbol": "+",
        "symbolSize": 12,
    }
]


class _1D_plot:
    def __init__(self, dataset, y_key, logmode):
        """
        plot 1D plot

        Args:
            ds_descr (list<dataset_data_description>) : list descriptions of the data to be plotted in the same plot
            logmode dict(<str, bool>) : plot axis in a logaritmic scale (e.g. {'x':True, 'y':False})
        """
        self.dataset = dataset
        self.y_key = y_key
        self.logmode = logmode

        pg.setConfigOption("background", None)
        pg.setConfigOption("foreground", "k")

        self.widget = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()

        self.plot = pg.PlotWidget()
        self.label = QtWidgets.QLabel()
        self.label.setAlignment(QtCore.Qt.AlignRight)

        self.layout.addWidget(self.plot)
        self.layout.addWidget(self.label)
        self.widget.setLayout(self.layout)

        self.curves = []

        self.plot.addLegend()

        # Removed loop over multiple values
        curve = self.plot.plot(
            *self.get_x_and_y(dataset, y_key),
            **graph_color[0],
            name=dataset[y_key].name,
            connect="finite"
        )
        self.curves.append(curve)

        self.plot.setLabel(
            "left",
            self.dataset[y_key].long_name,
            units=format_unit(self.dataset[y_key].attrs["units"]),
        )
        self.plot.setLabel(
            "bottom",
            self.dataset.x0.long_name,
            units=format_unit(self.dataset.x0.attrs["units"]),
        )
        self.plot.setLogMode(**logmode)
        self.plot.showGrid(True, True)
        if self.dataset[y_key].attrs["units"] == "%":
            self.plot.setYRange(0, 1)
        self.proxy = pg.SignalProxy(
            self.plot.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved
        )

    def update(self):
        for i in range(len(self.curves)):
            curve = self.curves[i]
            # ds = self.ds_list[i]
            curve.setData(*self.get_x_and_y(self.dataset, self.y_key), connect="finite")

    @property
    def name(self):
        name = "Plotting "
        name += " {}".format(self.dataset.name)

        return name[:-1]

    def get_x_and_y(self, ds, y_key: str):
        return ds.x0.values * return_unit_scaler(ds.x0.attrs["units"]), ds[
            y_key
        ].values * return_unit_scaler(ds[y_key].attrs["units"])

    def mouseMoved(self, evt):
        vb = self.plot.getPlotItem().vb
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.plot.sceneBoundingRect().contains(pos):
            mousePoint = vb.mapSceneToView(pos)
            index = int(mousePoint.x())

            x_val = mousePoint.x()
            if self.logmode["x"] == True:
                x_val = 10**x_val
            y_val = mousePoint.y()
            if self.logmode["y"] == True:
                y_val = 10**y_val

            self.label.setText(
                "x={}, y={}".format(
                    format_value_and_unit(x_val, self.dataset.x0.attrs["units"]),
                    format_value_and_unit(
                        y_val, self.dataset[self.y_key].attrs["units"]
                    ),
                )
            )
