from PyQt5 import QtCore, QtWidgets
import logging
from datetime import datetime, timedelta

from quantifiles.generate_mparam_ui_box import single_m_param_m_descriptor
from quantifiles.plots._1D_plotting import _1D_plot
from quantifiles.plots._2D_plotting import _2D_plot
from quantifiles.ui_files import plotter_basic_autgen

logger = logging.getLogger(__name__)


class data_plotter(QtWidgets.QMainWindow, plotter_basic_autgen.Ui_MainWindow):
    def __init__(self, ds):
        try:
            self.ds = ds
            self.alive = True
            self.app = QtCore.QCoreApplication.instance()
            self.instance_ready = True
            if self.app is None:
                self.instance_ready = False
                self.app = QtWidgets.QApplication([])

            super(QtWidgets.QMainWindow, self).__init__()
            self.setupUi(self)
            self.ui_box_mgr = ui_box_mgr(self.app, self.ds, self.data_plot_layout)

            gettables = [name for name in self.ds.data_vars.keys()]
            for name in gettables:
                layout = single_m_param_m_descriptor(
                    self.ds, name, self.scrollAreaWidgetContents_4
                )
                self.ui_box_mgr.add_m_param_plot_mgr(layout.plot_data_mgr)
                self.data_content_layout.addLayout(layout)

            verticalSpacer = QtWidgets.QSpacerItem(
                20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
            )
            self.data_content_layout.addItem(verticalSpacer)

            # render plots
            self.ui_box_mgr.draw_plots()

            self.show()

            if self.instance_ready == False:
                self.app.exec()
        except:
            logger.error(f"Data plotter", exc_info=True)

    def closeEvent(self, event):
        self.alive = False
        self.ui_box_mgr.close()


class ui_box_mgr:
    def __init__(self, app, ds, plot_layout):
        """
        Manager that will generate the plots (connecting the selected settings from the user with the pyqtgraph plotting library

        Args:
            app
            plot_layout (tbd) : qt layout where the pyqt windows can be inserted in.
        """
        self.plot_layout = plot_layout
        self.m_param_plot_mgr = []
        self.timer = QtCore.QTimer()
        self.plot_widgets = []
        self.app = app
        self.ds = ds

    def add_m_param_plot_mgr(self, mgr):
        """
        type:data_mgr_4_plot
        """
        self.m_param_plot_mgr.append(mgr)
        mgr.parent = self

    def draw_plots(self):
        self.timer.stop()
        self.plot_layout.parentWidget().setUpdatesEnabled(False)

        # clear all
        plot_widgets = []
        for item in self.m_param_plot_mgr:
            if item.show_plot:
                if item.n_dim == 1 and item.enable:
                    plot_widget = _1D_plot(
                        item.ds, item.y_key, {"x": item.x_log, "y": item.y_log}
                    )
                    plot_widgets.append(plot_widget)

                if item.n_dim == 2 and item.enable:
                    plot_widget = _2D_plot(item.ds, y_key=item.y_key, logmode={"z": item.z_log})
                    plot_widgets.append(plot_widget)
                    histogram = plot_widget.img_view.ui.histogram
                    if not item.show_histogram:
                        if not histogram.isHidden():
                            histogram.hide()
                    else:
                        if histogram.isHidden():
                            histogram.show()

        for i in reversed(range(self.plot_layout.count())):
            widgetToRemove = self.plot_layout.itemAt(i).widget()
            self.plot_layout.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)

        self.plot_widgets = plot_widgets
        for plot_widget in self.plot_widgets:
            self.plot_layout.addWidget(plot_widget.widget)
        # update plot every 300 ms for a smooth plotting experience

        self.plot_layout.parentWidget().setUpdatesEnabled(True)
        # if not self.ds.completed and datetime.now() - self.ds.run_timestamp < timedelta(
        #         days=1
        # ):
        if True:  # TODO: fix this
            self.timer.timeout.connect(self.update_plots)
            self.timer.start(300)

    def update_plots(self):
        # if self.ds.completed:  # TODO: fix this
        #     self.timer.stop()

        # self.ds.sync()

        for plot in self.plot_widgets:
            try:
                plot.update()
            except:
                logger.error(f"Plot update failed", exc_info=True)

    def close(self):
        self.timer.stop()
