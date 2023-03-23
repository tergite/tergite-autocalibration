from __future__ import annotations

from PyQt5 import QtWidgets, QtCore
from quantify_core.data.types import TUID


class PlotHeader(QtWidgets.QWidget):
    def __init__(
        self,
        name: str,
        tuid: str | TUID,
        additional_info: str = "",
        parent: QtWidgets.QWidget | None = None,
    ):
        super().__init__(parent)
        self._name_label = QtWidgets.QLabel(f"Name: {name}", parent=self)
        self._name_label.setStyleSheet("font-size: 12px;")
        self._name_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self._name_label.setWordWrap(True)

        self._tuid_label = QtWidgets.QLabel(f"TUID: {str(tuid)}", parent=self)
        self._tuid_label.setStyleSheet("font-size: 12px;")
        self._name_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        self._tuid_label.setWordWrap(True)

        self._additional_info_label = QtWidgets.QLabel(additional_info, parent=self)
        self._additional_info_label.setStyleSheet("font-size: 12px;")
        self._additional_info_label.setWordWrap(True)
        self._additional_info_label.setAlignment(QtCore.Qt.AlignCenter)

        self._layout = QtWidgets.QGridLayout()
        self._layout.addWidget(self._name_label, 0, 0)
        self._layout.addWidget(self._tuid_label, 0, 1)
        self._layout.addWidget(self._additional_info_label, 1, 0, 1, 2)

        self._layout.setColumnStretch(0, 1)
        self._layout.setColumnStretch(1, 1)

        self.setLayout(self._layout)

    def set_additional_info(self, text: str) -> None:
        self._additional_info_label.setText(text)
