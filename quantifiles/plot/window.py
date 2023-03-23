from __future__ import annotations

import logging
from functools import partial

import xarray as xr

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QSignalMapper

from quantifiles.data import get_snapshot_as_dict

logger = logging.getLogger(__name__)


class SingleGettableBox(QtWidgets.QFrame):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        gettable_name: str = "",
        dataset: xr.Dataset | None = None,
    ):
        super().__init__(parent)
        gettable_long_name = dataset[gettable_name].long_name
        gettable_units = dataset[gettable_name].attrs["units"]
        box_title = f"{gettable_name} {gettable_long_name} ({gettable_units})"

        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)

        grid_layout = QtWidgets.QGridLayout(self)
        param_table_layout = QtWidgets.QGridLayout(self)

        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setChecked(True)

        label = QtWidgets.QLabel(box_title)
        underline = QtWidgets.QFrame()
        underline.setFrameShape(QtWidgets.QFrame.HLine)
        underline.setFrameShadow(QtWidgets.QFrame.Sunken)

        grid_layout.addWidget(self.checkbox, 0, 0)
        grid_layout.addWidget(label, 0, 1)
        grid_layout.addWidget(underline, 1, 1)

        grid_layout.addLayout(param_table_layout, 2, 1)

        for idx, settable_name in enumerate(dataset[gettable_name].coords.keys()):
            settable_long_name = dataset[gettable_name][settable_name].long_name

            label_short_name = QtWidgets.QLabel(str(settable_name))
            label_long_name = QtWidgets.QLabel(str(settable_long_name))
            label_settable_unit = QtWidgets.QLabel(
                str(dataset[gettable_name][settable_name].attrs["units"])
            )

            param_table_layout.addWidget(label_short_name, idx, 0)
            param_table_layout.addWidget(label_long_name, idx, 1)
            param_table_layout.addWidget(label_settable_unit, idx, 2)

        content = QtWidgets.QWidget(self)
        content.setLayout(grid_layout)
        spacer = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        content_layout = QtWidgets.QHBoxLayout(self)
        content_layout.addSpacerItem(spacer)
        content_layout.addWidget(content)
        content_layout.addSpacerItem(spacer)
        self.setLayout(content_layout)


class GettableSelectBox(QtWidgets.QFrame):
    gettable_toggled = QtCore.pyqtSignal(str, bool)

    def __init__(
        self, parent: QtWidgets.QWidget | None = None, dataset: xr.Dataset | None = None
    ):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel("Dataset contents:")
        spacer = QtWidgets.QSpacerItem(
            25, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        layout.addSpacerItem(spacer)
        layout.addWidget(label)

        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setLayout(layout)

        self.gettable_select_mapper = QSignalMapper()
        self.gettable_select_mapper.mapped[str].connect(self.gettable_state_changed)

        self._gettable_checkboxes = {}
        for idx, gettable_name in enumerate(dataset.data_vars.keys()):
            gettable_box = SingleGettableBox(
                gettable_name=gettable_name, dataset=dataset
            )
            gettable_box.checkbox.stateChanged.connect(self.gettable_select_mapper.map)
            self.gettable_select_mapper.setMapping(gettable_box.checkbox, gettable_name)
            self._gettable_checkboxes[gettable_name] = gettable_box.checkbox

            layout.addWidget(
                gettable_box,
            )
        layout.addSpacerItem(spacer)

    def gettable_state_changed(self, name: str):
        enabled = self._gettable_checkboxes[name].isChecked()
        self.gettable_toggled.emit(name, enabled)


class NameAndTuidBox(QtWidgets.QFrame):
    def __init__(self, name: str, tuid: str):
        super().__init__()
        self.name = name
        self.tuid = tuid

        # --- Set up frame ---
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        layout = QtWidgets.QVBoxLayout(self)

        # --- Name and TUID labels ---
        self.name_label = QtWidgets.QLabel("Name:")
        self.name_label_content = QtWidgets.QLabel(self.name)
        self.name_label_content.setMargin(5)
        self.name_label_content.setFrameStyle(
            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken
        )
        self.name_label_content.setWordWrap(True)
        self.name_label_content.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.name_label_content.customContextMenuRequested.connect(
            partial(self.show_copy_context_menu, self.name)
        )

        self.tuid_label = QtWidgets.QLabel("TUID:")
        self.tuid_label_content = QtWidgets.QLabel(self.tuid)
        self.tuid_label_content.setMargin(5)
        self.tuid_label_content.setFrameStyle(
            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken
        )
        self.tuid_label_content.setWordWrap(True)
        self.tuid_label_content.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tuid_label_content.customContextMenuRequested.connect(
            partial(self.show_copy_context_menu, self.tuid)
        )

        # --- Add to layout ---
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_label_content)

        layout.addWidget(self.tuid_label)
        layout.addWidget(self.tuid_label_content)

        self.setLayout(layout)

    def show_copy_context_menu(self, value: str, pos: QtCore.QPoint):
        menu = QtWidgets.QMenu()

        copy_action = menu.addAction("Copy")
        action = menu.exec_(self.tuid_label_content.mapToGlobal(pos))
        if action == copy_action:
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(value)


class PlotTab(QtWidgets.QWidget):
    def __init__(self, dataset: xr.Dataset | None):
        super().__init__()
        self.dataset = dataset
        self.gettable_select_box = GettableSelectBox(dataset=dataset)
        self.name_and_tuid_box = NameAndTuidBox(name=dataset.name, tuid=dataset.tuid)

        layout = QtWidgets.QHBoxLayout(self)

        left_column_layout = QtWidgets.QVBoxLayout(self)
        left_column_layout.addWidget(self.name_and_tuid_box)
        left_column_layout.addWidget(self.gettable_select_box)

        layout.addLayout(left_column_layout)
        self.setLayout(layout)

    def add_plot(self, plot: QtWidgets.QWidget):
        self.layout().addWidget(plot)


class SnapshotTab(QtWidgets.QWidget):
    def __init__(self, snapshot: dict[str, any]):
        super().__init__()
        self.snapshot = snapshot

        layout = QtWidgets.QVBoxLayout(self)

        self.snapshot_tree = QtWidgets.QTreeWidget()
        self.snapshot_tree.setHeaderLabels(["Name", "Value"])
        self.snapshot_tree.setColumnWidth(0, 200)
        self.snapshot_tree.setSortingEnabled(True)
        self.snapshot_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.snapshot_tree.customContextMenuRequested.connect(
            self.show_copy_context_menu
        )

        self.add_snapshot_to_tree(self.snapshot_tree, self.snapshot)

        layout.addWidget(self.snapshot_tree)
        self.setLayout(layout)

    def add_snapshot_to_tree(
        self,
        tree: QtWidgets.QTreeWidget,
        snapshot: dict[str, any],
        parent_key: str = "",
    ):
        for key, value in snapshot.items():
            if isinstance(value, dict):
                item = QtWidgets.QTreeWidgetItem(tree)
                item.setText(0, key)
                self.add_snapshot_to_tree(item, value, key)
            else:
                item = QtWidgets.QTreeWidgetItem(tree)
                item.setText(0, f"{parent_key}.{key}" if parent_key else key)
                item.setText(1, str(value))

    def show_copy_context_menu(self, pos: QtCore.QPoint):
        menu = QtWidgets.QMenu()

        copy_action = menu.addAction("Copy")
        action = menu.exec_(self.snapshot_tree.mapToGlobal(pos))
        if action == copy_action:
            current_item = self.snapshot_tree.currentItem()
            item_parent = current_item.parent()
            if item_parent is not None:
                dict_copy = {}
                for i in range(item_parent.childCount()):
                    child_item = item_parent.child(i)
                    key = child_item.text(0).split(".", 1)[
                        -1
                    ]  # Strip parent key from child key
                    value = child_item.text(1)
                    dict_copy[key] = value
                clipboard = QtWidgets.QApplication.clipboard()
                clipboard.setText(str(dict_copy))


class PlotWindowContent(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        dataset: xr.Dataset | None = None,
        snapshot: dict[str, any] | None = None,
    ):
        super().__init__(parent)

        # Create the tab widget
        tab_widget = QtWidgets.QTabWidget()
        tab_widget.setTabPosition(QtWidgets.QTabWidget.West)
        tab_widget.setTabShape(QtWidgets.QTabWidget.Rounded)

        # Create the tab content
        self.plot_tab = PlotTab(dataset=dataset)

        # Add the tabs
        tab_widget.addTab(self.plot_tab, "Plots")
        if snapshot is not None:
            logger.debug("Adding snapshot tab")
            tab_widget.addTab(SnapshotTab(snapshot=snapshot), "Snapshot")

        # Set the layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(tab_widget)

        self.setLayout(layout)

    def add_plot(self, plot: QtWidgets.QWidget):
        self.plot_tab.add_plot(plot)


class PlotWindow(QtWidgets.QMainWindow):
    _WINDOW_TITLE: str = "Quantifiles plot window"
    _WINDOW_SIZE: int = 200

    def __init__(self, dataset: xr.Dataset, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.dataset = dataset
        self.plots = {}

        tuid = self.dataset.tuid if hasattr(self.dataset, "tuid") else "no tuid"
        name = self.dataset.name if hasattr(self.dataset, "name") else "no name"
        self.snapshot = get_snapshot_as_dict(tuid)

        self.setWindowTitle(f"{self._WINDOW_TITLE} | {name} | {tuid}")
        logger.debug(
            f"Initialized {self.__class__.__name__} with title: {self.windowTitle()}"
        )

        canvas = PlotWindowContent(self, dataset=dataset, snapshot=self.snapshot)
        self.canvas = canvas
        self.setCentralWidget(canvas)

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setMinimumSize(self._WINDOW_SIZE, self._WINDOW_SIZE)

        canvas.plot_tab.gettable_select_box.gettable_toggled.connect(
            self.toggle_gettable
        )

    def add_plot(self, name: str, plot: QtWidgets.QWidget):
        self.canvas.add_plot(plot)
        self.plots[name] = plot

        logger.debug(f"Added plot with name {name} to {self.__class__.__name__}")

    @QtCore.pyqtSlot(str, bool)
    def toggle_gettable(self, name: str, enabled: bool):
        self.plots[name].setVisible(enabled)

        logger.debug(f"Toggled visibility of plot with name {name} to {enabled}")
