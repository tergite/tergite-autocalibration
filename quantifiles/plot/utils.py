from __future__ import annotations

from pyqtgraph.widgets import PlotWidget


def set_label(plot: PlotWidget, axis: str, name: str, unit: str | None, default_unit: str):
    if unit is not None:
        plot.setLabel(
            axis,
            name,
            units=unit,
        )
    else:
        plot.setLabel(
            axis,
            f"{name} ({default_unit})",
        )
