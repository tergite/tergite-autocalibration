from __future__ import annotations

import logging
from functools import partial
from typing import cast

import xarray as xr

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import QSignalMapper

from quantifiles.data import get_snapshot_as_dict
from quantifiles.plot.baseplot import BasePlot
from quantifiles.plot.lineplot import LinePlot
from quantifiles.plot.snapshot import SnapshotTab

class QubitSelector(QtWidgets.QWidget):

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        qubit_name: str = "",
        dataset: xr.Dataset | None = None,
    ):
        super().__init__(parent)

        # Get the long name and units of the data variable.
        # gettable_long_name = dataset[gettable_name].long_name
        # gettable_units = dataset[gettable_name].attrs["units"]
        # box_title = f"{gettable_name}: {gettable_long_name} ({gettable_units})"
        box_title = qubit_name

        # Set up the main layout of the widget.
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Set up the checkbox for selecting the data variable.
        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.setToolTip(f"Select to include {qubit_name} in plot")
        self.checkbox.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum
        )

        checkbox_layout = QtWidgets.QVBoxLayout()
        checkbox_layout.addWidget(self.checkbox)
        checkbox_layout.setAlignment(QtCore.Qt.AlignRight)


        # Set up the box containing the variable selection options.
        box_layout = QtWidgets.QVBoxLayout()

        # Add the title label and underline.
        label = QtWidgets.QLabel(box_title)
        underline = QtWidgets.QFrame()
        underline.setFrameShape(QtWidgets.QFrame.HLine)
        underline.setFrameShadow(QtWidgets.QFrame.Sunken)

        box_layout.addWidget(label)
        box_layout.addWidget(underline)

        # Add a label for each settable variable.
        # for row_index, settable_name in enumerate(dataset[gettable_name].coords.keys()):
        #     settable_long_name = dataset[gettable_name][settable_name].long_name
        #     settable_units = dataset[gettable_name][settable_name].attrs["units"]
        #     settable_label = QtWidgets.QLabel(
        #         f"{settable_name}: {settable_long_name} ({settable_units})"
        #     )
        #     box_layout.addWidget(settable_label)

        # Set up the box frame and add it to the main layout.
        box_frame = QtWidgets.QFrame(self)
        box_frame.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Sunken)
        box_frame.setLayout(box_layout)
        box_frame.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )

        main_layout.addLayout(checkbox_layout)
        main_layout.addWidget(box_frame)
