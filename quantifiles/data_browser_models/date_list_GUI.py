from PyQt5 import QtCore, QtGui, QtWidgets


class data_list_model(QtCore.QAbstractListModel):
    def __init__(self):
        super().__init__()

        self.data_list = []
        self.items_displayed = 0

    def rowCount(self, index):
        return self.items_displayed

    def data(self, index, role):
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            return self.data_list[index.row()].strftime("%d/%m/%Y")

        return None

    def canFetchMore(self, index):
        return self.items_displayed < len(self.data_list)

    def fetchMore(self, index):
        remainder = len(self.data_list) - self.items_displayed
        itemsToFetch = min(50, remainder)

        self.beginInsertRows(
            QtCore.QModelIndex(),
            self.items_displayed,
            self.items_displayed + itemsToFetch,
        )
        self.items_displayed += itemsToFetch
        self.endInsertRows()

    def update_content(self, data):
        import numpy as np

        self.beginResetModel()
        self.items_displayed = 0
        self.data_list = data
        self.endResetModel()
