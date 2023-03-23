from __future__ import annotations

from PyQt5 import QtWidgets, QtCore
from quantify_core.data.types import TUID


class PlotHeader(QtWidgets.QWidget):
    """
    A custom widget to display a plot header with a name, TUID, and additional information.
    """

    def __init__(
        self,
        name: str,
        tuid: str | TUID,
        additional_info: str = "",
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """
        Initialize the plot header with the given name, TUID, and additional information.

        Parameters
        ----------
        name : str
            The name of the plot.
        tuid : str | TUID
            The TUID of the plot.
        additional_info : str, optional
            Additional information about the plot. Defaults to "".
        parent : QtWidgets.QWidget | None, optional
            The parent widget. Defaults to None.
        """
        super().__init__(parent)

        # Create the name label widget
        self._name_label = QtWidgets.QLabel(f"Name: {name}", parent=self)
        self._name_label.setStyleSheet("font-size: 12px;")
        self._name_label.setWordWrap(True)

        # Create the TUID label widget
        self._tuid_label = QtWidgets.QLabel(f"TUID: {str(tuid)}", parent=self)
        self._tuid_label.setStyleSheet("font-size: 12px;")
        self._tuid_label.setWordWrap(True)
        self._tuid_label.setAlignment(QtCore.Qt.AlignRight)

        # Create the additional information label widget
        self._additional_info_label = QtWidgets.QLabel(additional_info, parent=self)
        self._additional_info_label.setStyleSheet("font-size: 12px;")
        self._additional_info_label.setWordWrap(True)
        self._additional_info_label.setAlignment(QtCore.Qt.AlignCenter)

        # Create the layout and add the widgets to it
        self._layout = QtWidgets.QGridLayout()
        self._layout.addWidget(self._name_label, 0, 0)
        self._layout.addWidget(self._tuid_label, 0, 1)
        self._layout.addWidget(self._additional_info_label, 1, 0, 1, 2)

        # Set the stretch factor of the columns in the layout
        self._layout.setColumnStretch(0, 1)
        self._layout.setColumnStretch(1, 1)

        # Set the layout for the plot header
        self.setLayout(self._layout)

    def set_additional_info(self, text: str) -> None:
        """
        Set the additional information label text.

        Parameters
        ----------
        text : str
            The text to set as the additional information label.
        """
        self._additional_info_label.setText(text)

