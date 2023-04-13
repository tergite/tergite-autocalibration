from __future__ import annotations

from PyQt5 import QtWidgets, QtCore


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
