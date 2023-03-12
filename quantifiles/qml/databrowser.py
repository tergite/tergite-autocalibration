from __future__ import annotations

from pathlib import Path

from PyQt5 import QtCore, QtWidgets, QtQml, QtGui
import os
import platform
import ctypes

from quantify_core.data.handling import set_datadir

from quantifiles.qml.gui_control import DataFilter, SignalHandler
from quantifiles.qml.models import date_model, data_overview_model, combobox_model
import quantifiles.qml as qml_in


class DataBrowser:
    def __init__(
        self,
        data_dir: str | Path,
        window_location=None,
        window_size=None,
        live_plotting_enabled=True,
    ):
        set_datadir(data_dir)
        set_app_icon()

        self.app = QtCore.QCoreApplication.instance()
        self.instance_ready = True
        if self.app is None:
            self.instance_ready = False
            QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
            self.app = QtWidgets.QApplication([])

        self.app.setFont(QtGui.QFont("Sans Serif", 8))
        self.engine = QtQml.QQmlApplicationEngine()

        self.date_model = date_model([])
        self.data_overview_model = data_overview_model([])

        self.project_model = combobox_model()
        self.set_up_model = combobox_model()
        self.sample_model = combobox_model()

        self.data_filter = DataFilter(
            self.project_model, self.set_up_model, self.sample_model
        )

        self.signal_handler = SignalHandler(
            self.data_filter,
            self.date_model,
            self.data_overview_model,
            live_plotting_enabled=live_plotting_enabled,
        )

        self.engine.rootContext().setContextProperty(
            "combobox_project_model", self.project_model
        )
        self.engine.rootContext().setContextProperty(
            "combobox_set_up_model", self.set_up_model
        )
        self.engine.rootContext().setContextProperty(
            "combobox_sample_model", self.sample_model
        )

        self.engine.rootContext().setContextProperty("date_list_model", self.date_model)
        self.engine.rootContext().setContextProperty(
            "data_content_view_model", self.data_overview_model
        )

        self.engine.rootContext().setContextProperty("local_conn_status", True)
        self.engine.rootContext().setContextProperty("remote_conn_status", True)

        self.engine.rootContext().setContextProperty(
            "signal_handler", self.signal_handler
        )

        # grab directory from the import!
        filename = os.path.join(os.path.dirname(qml_in.__file__), "data_browser.qml")

        self.engine.load(QtCore.QUrl.fromLocalFile(filename))
        self.win = self.engine.rootObjects()[0]
        self.signal_handler.init_gui_variables(self.win)
        if window_location is not None:
            self.win.setPosition(window_location[0], window_location[1])
        if window_size is not None:
            self.win.setWidth(window_size[0])
            self.win.setHeight(window_size[1])

        if not self.instance_ready:
            self.app.exec_()


def set_app_icon():
    if platform.system() == "Windows":
        myappid = "quantifiles_databrowser"  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


if __name__ == "__main__":
    databrowser = DataBrowser(r"C:\Users\Damie\PycharmProjects\quantifiles\test_data")
