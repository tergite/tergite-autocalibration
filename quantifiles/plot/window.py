from __future__ import annotations

import logging
from functools import partial

import xarray as xr

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QSignalMapper

from quantifiles.data import get_snapshot_as_dict
from quantifiles.plot.baseplot import BasePlot

logger = logging.getLogger(__name__)


class GettableSelector(QtWidgets.QWidget):
    """
    A widget for selecting variables in a given xarray dataset.

    Parameters
    ----------
    parent : QtWidgets.QWidget or None, optional
        The parent widget of the selector. If None, it will be a top-level widget.
    gettable_name : str, optional
        The name of the xarray data variable to be selected.
    dataset : xarray.Dataset or None, optional
        The xarray dataset containing the data variable to be selected.

    Attributes
    ----------
    checkbox : QtWidgets.QCheckBox
        The checkbox used to select the data variable.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        gettable_name: str = "",
        dataset: xr.Dataset | None = None,
    ):
        super().__init__(parent)

        # Get the long name and units of the data variable.
        gettable_long_name = dataset[gettable_name].long_name
        gettable_units = dataset[gettable_name].attrs["units"]
        box_title = f"{gettable_name}: {gettable_long_name} ({gettable_units})"

        # Set up the main layout of the widget.
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Set up the checkbox for selecting the data variable.
        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.setToolTip(f"Select to include {gettable_name} in plot")
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
        for row_index, settable_name in enumerate(dataset[gettable_name].coords.keys()):
            settable_long_name = dataset[gettable_name][settable_name].long_name
            settable_units = dataset[gettable_name][settable_name].attrs["units"]
            settable_label = QtWidgets.QLabel(
                f"{settable_name}: {settable_long_name} ({settable_units})"
            )
            box_layout.addWidget(settable_label)

        # Set up the box frame and add it to the main layout.
        box_frame = QtWidgets.QFrame(self)
        box_frame.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Sunken)
        box_frame.setLayout(box_layout)
        box_frame.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )

        main_layout.addLayout(checkbox_layout)
        main_layout.addWidget(box_frame)


class GettableSelectBox(QtWidgets.QFrame):
    """
    A widget for selecting data variables from an xarray Dataset.
    """

    # Custom signal that is emitted when a checkbox is toggled
    gettable_toggled = QtCore.pyqtSignal(str, bool)

    def __init__(
        self, parent: QtWidgets.QWidget | None = None, dataset: xr.Dataset | None = None
    ):
        """
        Initialize the GettableSelectBox widget.

        Parameters
        ----------
        parent : QWidget or None
            The parent widget of this widget.
        dataset : xarray.Dataset or None
            The dataset containing the data variables to select.
        """
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)

        # Add a label to the top of the widget
        label = QtWidgets.QLabel("Dataset contents:")
        layout.addWidget(label)

        # Add a spacer to push the rest of the widgets down
        spacer = QtWidgets.QSpacerItem(
            25, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        layout.addSpacerItem(spacer)

        # Set the style and size policy of this widget
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setLayout(layout)

        # Create a signal mapper to map signals from the checkbox to the gettable name
        self.gettable_select_mapper = QSignalMapper()
        self.gettable_select_mapper.mapped[str].connect(self.gettable_state_changed)

        self._gettable_checkboxes = {}

        # Add a GettableSelector widget for each data variable in the dataset
        for idx, gettable_name in enumerate(dataset.data_vars.keys()):
            gettable_box = GettableSelector(
                gettable_name=gettable_name, dataset=dataset
            )

            # Connect the checkbox in the GettableSelector widget to the signal mapper
            gettable_box.checkbox.stateChanged.connect(self.gettable_select_mapper.map)
            self.gettable_select_mapper.setMapping(gettable_box.checkbox, gettable_name)

            self._gettable_checkboxes[gettable_name] = gettable_box.checkbox

            layout.addWidget(gettable_box)

        # Add another spacer to push the widgets so that they are centered
        layout.addSpacerItem(spacer)

        underline = QtWidgets.QFrame()
        underline.setFrameShape(QtWidgets.QFrame.HLine)
        underline.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(underline)

        self.mouse_pos_label = QtWidgets.QLabel()
        self.mouse_pos_label.setWordWrap(True)
        self.mouse_pos_label.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        layout.addWidget(self.mouse_pos_label)

    def on_new_mouse_pos_text(self, text: str):
        self.mouse_pos_label.setText(str(text))

    def gettable_state_changed(self, name: str):
        """
        Emit the gettable_toggled signal with the name of the toggled checkbox and its state.

        Parameters
        ----------
        name : str
            The name of the data variable associated with the toggled checkbox.
        """
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

        left_column_layout = QtWidgets.QVBoxLayout(self)
        left_column_layout.addWidget(self.name_and_tuid_box)
        left_column_layout.addWidget(self.gettable_select_box)

        column_container = QtWidgets.QWidget()
        column_container.setLayout(left_column_layout)

        self.plot_layout = QtWidgets.QHBoxLayout(self)
        plot_container = QtWidgets.QWidget()
        plot_container.setLayout(self.plot_layout)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(column_container)
        splitter.addWidget(plot_container)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(splitter)
        self.setLayout(layout)

    def add_plot(self, plot: QtWidgets.QWidget):
        self.plot_layout.addWidget(plot)
        plot.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )


class SnapshotTab(QtWidgets.QWidget):
    def __init__(self, snapshot: dict[str, any]):
        super().__init__()
        self.snapshot = snapshot

        layout = QtWidgets.QVBoxLayout(self)

        self.snapshot_tree = QtWidgets.QTreeWidget()
        self.snapshot_tree.setHeaderLabels(["Name", "Value"])
        self.snapshot_tree.setColumnWidth(0, 256)
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
    _WINDOW_HEIGHT: int = 600
    _WINDOW_WIDTH: int = 300

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

        canvas.plot_tab.gettable_select_box.gettable_toggled.connect(
            self.toggle_gettable
        )

    def add_plot(self, name: str, plot: BasePlot):
        self.canvas.add_plot(plot)
        self.plots[name] = plot
        plot.mouse_text_changed.connect(
            self.canvas.plot_tab.gettable_select_box.on_new_mouse_pos_text
        )

        self.resize(self._WINDOW_WIDTH + self._WINDOW_HEIGHT * len(self.plots), self._WINDOW_HEIGHT)

        logger.debug(f"Added plot with name {name} to {self.__class__.__name__}")

    @QtCore.pyqtSlot(str, bool)
    def toggle_gettable(self, name: str, enabled: bool):
        self.plots[name].setVisible(enabled)

        logger.debug(f"Toggled visibility of plot with name {name} to {enabled}")
