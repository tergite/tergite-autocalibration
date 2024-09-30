from __future__ import annotations
from functools import partial
import logging
from typing import Any, cast

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSignalMapper
import xarray as xr

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
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
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
        # box_layout.addWidget(underline)

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
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )

        main_layout.addLayout(checkbox_layout)
        main_layout.addWidget(box_frame)


class QubitSelectBox(QtWidgets.QFrame):
    """
    A widget for selecting data variables from an xarray Dataset.
    """

    # Custom signal that is emitted when a checkbox is toggled
    gettable_toggled = QtCore.pyqtSignal(str, bool)


    def __init__(
        self, parent: QtWidgets.QWidget | None = None, dataset: xr.Dataset | None = None
    ):
        """
        Initialize the QubitSelectBox widget.

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
            25, 40, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        layout.addSpacerItem(spacer)

        # Set the style and size policy of this widget
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.setLayout(layout)

        # Create a signal mapper to map signals from the checkbox to the gettable name
        self.gettable_select_mapper = QSignalMapper()
        self.gettable_select_mapper.mapped[str].connect(self.gettable_state_changed)

        self._gettable_checkboxes = {}

        all_qubits_box = QubitSelector(qubit_name='all qubits', dataset=dataset)
        all_qubits_box.checkbox.stateChanged.connect(self.gettable_select_mapper.map)
        self.gettable_select_mapper.setMapping(all_qubits_box.checkbox, 'all qubits')
        self._gettable_checkboxes['all qubits'] = all_qubits_box.checkbox
        layout.addWidget(all_qubits_box)

        # Add a GettableSelector widget for each data variable in the dataset
        qubits = set([dataset[coord].attrs['qubit'] for coord in dataset.coords])
        for qubit_name in qubits:
            qubit_box = QubitSelector(
                qubit_name=qubit_name, dataset=dataset
            )

            # Connect the checkbox in the QubitSelector widget to the signal mapper
            qubit_box.checkbox.stateChanged.connect(self.gettable_select_mapper.map)
            self.gettable_select_mapper.setMapping(qubit_box.checkbox, qubit_name)

            self._gettable_checkboxes[qubit_name] = qubit_box.checkbox

            layout.addWidget(qubit_box)

        # self.custom_select_box = CustomSelector(dataset=dataset)
        # self.custom_select_box.checkbox.stateChanged.connect(self.gettable_select_mapper.map)
        # layout.addWidget(self.custom_select_box)
        # Add another spacer to push the widgets so that they are centered
        layout.addSpacerItem(spacer)

        # the line above mouse position
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
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

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
        # self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.gettable_select_box = QubitSelectBox(dataset=dataset)
        self.name_and_tuid_box = NameAndTuidBox(name=dataset.name, tuid=dataset.tuid)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )

        left_column_layout = QtWidgets.QVBoxLayout(self)
        left_column_layout.addWidget(self.name_and_tuid_box)
        left_column_layout.addWidget(self.gettable_select_box)

        column_container = QtWidgets.QWidget()
        column_container.setLayout(left_column_layout)
        column_container.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        self.plot_layout = QtWidgets.QHBoxLayout(self)
        plot_container = QtWidgets.QWidget()
        plot_container.setLayout(self.plot_layout)
        plot_container.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        # splitter.addWidget(column_container)
        # splitter.addWidget(self.plot_container)
        # splitter.addWidget(secondary_plot_container)
        # splitter.setSizes([5, 295])

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(column_container)
        layout.addWidget(plot_container)
        # layout.addWidget(splitter)
        self.setLayout(layout)

    def add_plot(self, plot: QtWidgets.QWidget):
        self.plot_layout.addWidget(plot)
        plot.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        # plot.setFixedSize(200,200)


class DeviceTab(QtWidgets.QWidget):

    def __init__(self, device_config: dict[str, any]):
        """
        Initializes a new instance of the SnapshotTab class with the given snapshot dictionary.

        Parameters
        ----------
        snapshot : dict[str, any]
            The dictionary to display in the snapshot tab.
        """
        super().__init__()
        self.device_config = device_config

        # Set up the layout
        layout = QtWidgets.QVBoxLayout(self)

        # Add search bar
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        # self.search_bar.textChanged.connect(self.search_snapshot_tree)
        layout.addWidget(self.search_bar)

        # Set up the snapshot tree widget
        self.snapshot_tree = QtWidgets.QTreeWidget()
        self.snapshot_tree.setHeaderLabels(["Name", "Value"])
        self.snapshot_tree.setColumnWidth(0, 256)
        self.snapshot_tree.setSortingEnabled(True)
        self.snapshot_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.snapshot_tree.customContextMenuRequested.connect(
        #     self.show_copy_context_menu
        # )

        # Add the snapshot dictionary to the tree
        self.add_snapshot_to_tree(self.snapshot_tree, self.device_config)

        # Add the snapshot tree widget to the layout
        layout.addWidget(self.snapshot_tree)
        self.setLayout(layout)

    def add_snapshot_to_tree(
        self,
        tree: QtWidgets.QTreeWidget,
        snapshot: dict[str, any],
        parent_key: str = "",
    ):
        """
        Recursively adds the given snapshot dictionary to the given tree widget.

        Parameters
        ----------
        tree : QtWidgets.QTreeWidget
            The tree widget to add th        containerWidget = QWidget()e snapshot to.
        snapshot : dict[str, any]
            The snapshot dictionary to add to the tree.
        parent_key : str, optional
            The parent key to use when constructing the item keys, by default "".
        """
        for key, value in snapshot.items():
            if isinstance(value, dict):
                # If the value is another dictionary, add it as a child item
                item = QtWidgets.QTreeWidgetItem(tree)
                item.setText(0, key)
                self.add_snapshot_to_tree(item, value, key)
            else:
                # If the value is a non-dict type, add it as a leaf item
                item = QtWidgets.QTreeWidgetItem(tree)
                item.setText(0, f"{parent_key}.{key}" if parent_key else key)
                item.setText(1, str(value))




class PlotWindowContent(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        dataset: xr.Dataset | None = None,
        device_config: dict[str, Any] | None = None,
    ):
        super().__init__(parent)

        # Create the tab widget
        tab_widget = QtWidgets.QTabWidget()
        tab_widget.setTabPosition(QtWidgets.QTabWidget.West)
        tab_widget.setTabShape(QtWidgets.QTabWidget.Rounded)

        # Create the tab content
        self.plot_tab = PlotTab(dataset=dataset)
        self.plot_tab.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )

        self.device_tab = DeviceTab(device_config)

        # Add the tabs
        tab_widget.addTab(self.plot_tab, "Plots")
        tab_widget.addTab(self.device_tab, 'Device')
        # if device_config is not None:
        #     # logger.debug("Adding snapshot tab")
        #     tab_widget.addTab(SnapshotTab(snapshot=device_config), "Snapshot")

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

    def __init__(
            self,
            dataset: xr.Dataset,
            device_config: dict[str, Any] | None = None,
            parent: QtWidgets.QWidget | None = None
        ):
        super().__init__(parent)
        self.dataset = dataset
        self.device_config = device_config

        self.N_gettables = len(list(dataset.data_vars.keys()))
        self.plots = {}

        tuid = self.dataset.tuid if hasattr(self.dataset, "tuid") else "no tuid"
        name = self.dataset.name if hasattr(self.dataset, "name") else "no name"
        # self.snapshot = get_snapshot_as_dict(tuid)

        self.setWindowTitle(f"{self._WINDOW_TITLE} | {name} | {tuid}")
        # logger.debug(
        #     f"Initialized {self.__class__.__name__} with title: {self.windowTitle()}"
        # )

        canvas = PlotWindowContent(self, dataset=dataset, device_config=self.device_config)
        self.canvas = canvas
        self.setCentralWidget(canvas)

        canvas.plot_tab.gettable_select_box.gettable_toggled.connect(
            self.toggle_gettable
        )

        # canvas.plot_tab.gettable_select_box.custom_select_box.combo_selected.connect(
        #     self.plot_custom_graph
        # )

        # make sure the window is on top, and that it is activated. Does not always work on Windows due to Windows not
        # allowing this if the application is not the active window.
        self.show()
        self.raise_()
        self.activateWindow()

    def add_plot(self, name: str, plot: BasePlot):
        self.canvas.add_plot(plot)
        self.plots[name] = plot
        plot.mouse_text_changed.connect(
            self.canvas.plot_tab.gettable_select_box.on_new_mouse_pos_text
        )

        self.resize(
            self._WINDOW_WIDTH + self._WINDOW_HEIGHT * len(self.plots),
            self._WINDOW_HEIGHT,
        )

    def add_secondary_plot(self, name: str, plot: BasePlot):
        self.canvas.add_plot(plot)
        self.plots[name] = plot
        plot.mouse_text_changed.connect(
            self.canvas.plot_tab.gettable_select_box.on_new_mouse_pos_text
        )

        self.resize(
            self._WINDOW_WIDTH + self._WINDOW_HEIGHT * len(self.plots),
            self._WINDOW_HEIGHT,
        )

        # logger.debug(f"Added plot with name {name} to {self.__class__.__name__}")

    # def add_custom_plot(self, plot: BasePlot):
    #     current_layout = self.canvas.plot_tab.plot_layout
    #
    #     current_custom_plot = current_layout.itemAt(self.N_gettables)
    #     if current_custom_plot != None:
    #         widget = current_custom_plot.widget()
    #         if widget != None:
    #             current_layout.removeWidget(widget)
    #             widget.deleteLater()
    #
    #     self.canvas.add_plot(plot)
    #     plot.mouse_text_changed.connect(
    #         self.canvas.plot_tab.gettable_select_box.on_new_mouse_pos_text
    #     )
    #
    #     self.resize(
    #         self._WINDOW_WIDTH + self._WINDOW_HEIGHT * (1+len(self.plots)),
    #         self._WINDOW_HEIGHT,
    #     )

    @QtCore.pyqtSlot(str, bool)
    def toggle_gettable(self, name: str, enabled: bool):
        if name == 'all qubits':
            for name in self.plots.keys():
                self.plots[name].setVisible(enabled)
        else:
            self.plots[name].setVisible(enabled)
        # logger.debug(f"Toggled visibility of plot with name {name} to {enabled}")

    # @QtCore.pyqtSlot(str, str)
    # def plot_custom_graph(self, x_variable: str, y_variable: str):
    #     custom_plot = LinePlot(self.dataset, x_key=x_variable, y_keys=y_variable)
    #     self.add_custom_plot(custom_plot)
