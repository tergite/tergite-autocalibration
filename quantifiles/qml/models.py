from PyQt5 import QtCore

import os

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"


class date_model(QtCore.QAbstractListModel):
    def __init__(self, dates, parent=None):
        super().__init__(parent)
        self._dates = dates

    def rowCount(self, parent=None):
        return len(self._dates)

    def data(self, index, role):
        return self._dates[index.row()].strftime("%d/%m/%Y")

    def roleNames(self):
        return {
            QtCore.Qt.UserRole + 1: b"date",
        }

    def reset_data(self, dates):
        self.beginResetModel()
        self._dates = dates
        self.endResetModel()

    def __getitem__(self, item):
        return self._dates[item]


class data_overview_model(QtCore.QAbstractListModel):
    starred = QtCore.Qt.UserRole + 1
    my_ID = QtCore.Qt.UserRole + 2
    UUID = QtCore.Qt.UserRole + 3
    date = QtCore.Qt.UserRole + 4
    name = QtCore.Qt.UserRole + 5
    keywords = QtCore.Qt.UserRole + 6

    def __init__(self, model_data, parent=None):
        super().__init__(parent)
        self._data = model_data

    def rowCount(self, parent=None):
        return len(self._data)

    def data(self, QModelIndex, role):
        row = QModelIndex.row()
        if role == self.starred:
            return self._data[row].starred
        if role == self.my_ID:
            return self._data[row].my_id
        if role == self.UUID:
            # s = str(self._data[row].uuid)
            # return s[:-14] + "_" + s[-14:-9] + "_" + s[-9:]
            return self._data[row].uuid
        if role == self.name:
            return self._data[row].name
        if role == self.keywords:
            return self._data[row].keywords
        if role == self.date:
            return self._data[row].time

    def roleNames(self):
        return {
            QtCore.Qt.UserRole + 1: b"starred",
            QtCore.Qt.UserRole + 2: b"id_",
            QtCore.Qt.UserRole + 3: b"uuid",
            QtCore.Qt.UserRole + 4: b"date",
            QtCore.Qt.UserRole + 5: b"name",
            QtCore.Qt.UserRole + 6: b"keywords",
        }

    def reset_data(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()


class combobox_model(QtCore.QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._combobox_items = []

    def rowCount(self, parent=None):
        return len(self._combobox_items)

    def data(self, index, role):
        return self._combobox_items[index.row()]

    def roleNames(self):
        return {
            QtCore.Qt.UserRole + 1: b"text",
        }

    def reset_data(self, string_list):
        self.beginResetModel()
        self._combobox_items = string_list
        self.endResetModel()

    def __getitem__(self, item):
        return self._combobox_items[item]
