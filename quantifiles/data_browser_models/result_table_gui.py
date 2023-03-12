from PyQt5 import QtCore, QtGui, QtWidgets


class result_table_model(QtCore.QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._data = [[]]
        self.items_displayed = 0

    def overwrite_data(self, data):
        self._data = data
        self.items_displayed = 0
        self.layoutChanged.emit()

    def data(self, index, role):
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            return self._data[index.row()][index.column()]

        return None

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return (
                "ID",
                "UUID",
                "Name",
                "date",
                "Project",
                "Set up",
                "Sample",
                "Keywords",
                "location",
            )[section]
        if (
            orientation == QtCore.Qt.Horizontal
            and role == QtCore.Qt.InitialSortOrderRole
        ):
            if section == 3:
                return QtCore.Qt.DescendingOrder
            return None

        return None

    def rowCount(self, index):
        return self.items_displayed

    def columnCount(self, index):
        return len(self._data[0])

    def canFetchMore(self, index):
        return self.items_displayed < len(self._data)

    def fetchMore(self, index):
        remainder = len(self._data) - self.items_displayed
        itemsToFetch = min(50, remainder)
        self.beginInsertRows(
            QtCore.QModelIndex(),
            self.items_displayed,
            self.items_displayed + itemsToFetch - 1,
        )
        self.items_displayed += itemsToFetch
        self.endInsertRows()

    def sort(self, column, direction):
        self.layoutAboutToBeChanged.emit()
        self._data.sort(column, direction)
        self.layoutChanged.emit()
