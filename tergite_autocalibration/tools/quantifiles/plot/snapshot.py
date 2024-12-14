# BSD 2-Clause License
#
# Copyright (c) 2023, Damien Crielaard
# All rights reserved.

from __future__ import annotations

from PyQt5 import QtWidgets, QtCore


def find_matching_snapshot(
    snapshot: dict[str, any], search_term: str
) -> dict[str, any]:
    """Find all nodes in the snapshot that match the search term.

    Parameters
    ----------
    snapshot : dict[str, any]
        A dictionary representing the snapshot.
    search_term : str
        A string representing the search term.

    Returns
    -------
    dict[str, any]
        A dictionary containing all the nodes in the snapshot that match the search term.
    """

    matching_snapshot = {}

    for key, value in snapshot.items():
        if isinstance(value, dict):
            if search_term.lower() in key.lower():
                matching_snapshot[key] = value
            matching_sub_snapshot = find_matching_snapshot(value, search_term)
            if matching_sub_snapshot:
                matching_snapshot[key] = matching_sub_snapshot
        else:
            if search_term.lower() in key.lower():
                matching_snapshot[key] = value

    return matching_snapshot


class SnapshotTab(QtWidgets.QWidget):
    """
    A class representing a snapshot tab that displays a dictionary of values in a tree format.
    """

    def __init__(self, snapshot: dict[str, any]):
        """
        Initializes a new instance of the SnapshotTab class with the given snapshot dictionary.

        Parameters
        ----------
        snapshot : dict[str, any]
            The dictionary to display in the snapshot tab.
        """
        super().__init__()
        self.snapshot = snapshot

        # Set up the layout
        layout = QtWidgets.QVBoxLayout(self)

        # Add search bar
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.search_snapshot_tree)
        layout.addWidget(self.search_bar)

        # Set up the snapshot tree widget
        self.snapshot_tree = QtWidgets.QTreeWidget()
        self.snapshot_tree.setHeaderLabels(["Name", "Value"])
        self.snapshot_tree.setColumnWidth(0, 256)
        self.snapshot_tree.setSortingEnabled(True)
        self.snapshot_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.snapshot_tree.customContextMenuRequested.connect(
            self.show_copy_context_menu
        )

        # Add the snapshot dictionary to the tree
        self.add_snapshot_to_tree(self.snapshot_tree, self.snapshot)

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
            The tree widget to add the snapshot to.
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

    @QtCore.pyqtSlot(str)
    def search_snapshot_tree(self, search_term: str):
        """
        Searches the snapshot tree for items that match the given search term.

        Parameters
        ----------
        search_term : str
            The search term to use.
        """
        search_term = search_term.strip()
        if search_term:
            self.snapshot_tree.clear()
            matching_snapshot = find_matching_snapshot(self.snapshot, search_term)
            self.add_snapshot_to_tree(self.snapshot_tree, matching_snapshot)
        else:
            self.snapshot_tree.clear()
            self.add_snapshot_to_tree(self.snapshot_tree, self.snapshot)

    def show_copy_context_menu(self, pos: QtCore.QPoint) -> None:
        """Display the copy context menu.

        Parameters
        ----------
        pos : QtCore.QPoint
            The position of the cursor.

        Returns
        -------
        None
        """

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
                    key = child_item.text(0).split(".", 1)[-1]
                    value = child_item.text(1)
                    dict_copy[key] = value

                clipboard = QtWidgets.QApplication.clipboard()
                clipboard.setText(str(dict_copy))
