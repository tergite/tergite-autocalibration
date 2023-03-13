"""
This is a bit of messy file written in a hurry.
"""
from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial

from quantifiles.plots.unit_management import format_value_and_unit


class check_box_descriptor:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        check_box = getattr(obj, "_" + self.name)
        return self.checked_state_to_bool(check_box.checkState())

    def __set__(self, obj, value):
        check_box = getattr(obj, "_" + self.name)
        check_box.setCheckState(self.bool_to_checked_state(value))

    def checked_state_to_bool(self, state):
        return False if state == 0 else True

    def bool_to_checked_state(self, value):
        return 0 if value == False else 2


class n_th_dimension_prop(object):
    avg = check_box_descriptor()
    slc = check_box_descriptor()
    log = check_box_descriptor()
    """docstring for m_dimention_form_properties"""

    def __init__(self, name, long_name, avg, slc, log_scale, slider):
        self.name = name
        self.long_name = long_name

        self._avg = avg
        self._slc = slc
        self._log = log_scale
        self.slider = slider
        self._slc.clicked.connect(partial(self.slc_conn, "slc"))
        self._avg.clicked.connect(partial(self.update, "avg"))
        self._log.clicked.connect(partial(self.update, "log"))

        self.slider.connect_slider(self.update)
        self.parent = None

    @property
    def slider_val(self):
        return int(self.slider.slider.value())

    def slc_conn(self, *args):
        self.slider.set_visibilty(self.slc)
        self.update(args[0])

    def update(self, changer, *args):
        if self.avg == True and self.slc == True:
            if changer == "avg":
                self.slc = False
                self.slider.set_visibilty(self.slc)
            elif changer == "slc":
                self.avg = False

        if self.parent is not None:
            self.parent.update()

    def count(self):
        if self.avg == True or self.slc == True:
            return False
        return True


class slider_mgr:
    def __init__(self, name_shorthand, param, geom_parent):
        self.hbox = QtWidgets.QHBoxLayout()
        self.data_var = param
        self.slider = QtWidgets.QSlider(geom_parent)
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.name = name_shorthand + " slider"

        self.label_slider = QtWidgets.QLabel(geom_parent)
        self.label_slider.setText(name_shorthand + " slider")
        self.label_slider_content = QtWidgets.QLabel(geom_parent)

        self.hbox.setContentsMargins(10, 10, 10, 10)
        self.hbox.addWidget(self.label_slider)
        self.hbox.addWidget(self.slider)
        self.hbox.addWidget(self.label_slider_content)

        self.set_visibilty(False)

    def set_visibilty(self, state):
        self.slider.setVisible(state)
        self.label_slider.setVisible(state)
        self.label_slider_content.setVisible(state)

    def connect_slider(self, conn):
        self.label_slider_content.setText(
            format_value_and_unit(self.data_var.values[0], self.data_var.attrs["units"])
        )

        def slider_change(idx):
            self.label_slider_content.setText(
                format_value_and_unit(
                    self.data_var.values[idx], self.data_var.attrs["units"]
                )
            )
            conn(idx)

        self.slider.setTickInterval(1)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(self.data_var.values) - 1)
        self.slider.valueChanged.connect(slider_change)


class data_mgr_4_plot:
    def __init__(self, dataset, y_key: str = "y0"):
        self.dataset = dataset
        self._dataset = None
        self.y_key = y_key

        self.properties_selector_raw = []
        self.properties_selector = []
        self.parent = None
        self.enable = True
        self.show_plot = True
        self.show_histogram = False

    def add_properties(self, my_property):
        if len(self.properties_selector_raw) >= 2:
            my_property.avg = True
        self.properties_selector_raw += [my_property]

    def set_children(self):
        for prop in self.properties_selector_raw:
            prop.parent = self

        self.update()

    def update(self):
        properties = self.properties_selector_raw[:-1][::-1]

        self.properties_selector = []
        self._dataset = self.dataset

        for prop in properties:
            if prop.avg:
                self._dataset = self._dataset.average(prop.name)
            elif prop.slc:
                self._dataset = self._dataset.slice(prop.name, prop.slider_val)
            else:
                self.properties_selector.append(prop)

        for prop in properties:
            if self.n_dim == 1 and not prop.avg and not prop.slc:
                prop._log.setEnabled(True)
            else:
                prop._log.setEnabled(False)

        self.properties_selector = self.properties_selector[::-1] + [
            self.properties_selector_raw[-1]
        ]

        if self.parent is not None:
            self.parent.draw_plots()

    @property
    def x_log(self):
        return self.__check_log(0)

    @property
    def y_log(self):
        return self.__check_log(1)

    @property
    def z_log(self):
        return self.__check_log(2)

    def __check_log(self, dim):
        if dim > len(self._dataset.coords):
            return None
        return False  # FIXME: implement log scale

    @property
    def n_dim(self):
        return len(self._dataset.coords)

    def __add__(self, other):
        if isinstance(other, n_th_dimension_prop):
            self.add_properties(other)
        else:
            raise TypeError("bad type provided..")
        return self


class single_m_param_m_descriptor(QtWidgets.QVBoxLayout):
    def __init__(self, dataset, y_param: str, geom_parent):
        super().__init__()
        self.dataset = dataset
        self.geom_parent = geom_parent

        m_name = dataset[y_param].attrs["name"]
        label = dataset[y_param].attrs["long_name"]
        self.setObjectName(m_name + "m_param_box")

        self.m_param_1_title = QtWidgets.QLabel(self.geom_parent)
        self.m_param_1_title.setObjectName(m_name + "m_param_1_name")
        _translate = QtCore.QCoreApplication.translate
        self.m_param_1_title.setText(
            _translate("MainWindow", "{} ({})".format(m_name, label))
        )

        self.local_parent = QtWidgets.QGridLayout()
        self.local_parent.setObjectName(m_name + "single_meas_grid")

        self.generate_header(m_name)
        self.plot_data_mgr = data_mgr_4_plot(dataset, y_key=y_param)

        if len(self.dataset.coords) >= 2:
            self.cb_hist = QtWidgets.QCheckBox(self.geom_parent)
            self.cb_hist.setText("Show histogram")
            self.cb_hist.setObjectName(m_name + "_hist")
            self.cb_hist.clicked.connect(
                partial(self.cb_callback, self.cb_hist, "show_histogram")
            )
        else:
            self.cb_hist = None

        self.sp = QtWidgets.QCheckBox(self.geom_parent)
        self.sp.setText("")
        self.sp.setObjectName(m_name + "sp")
        self.sp.setMaximumSize(QtCore.QSize(16, 16777215))
        self.sp.setChecked(True)
        self.sp.clicked.connect(partial(self.cb_callback, self.sp, "show_plot"))

        settables = [
            name for name in dataset.variables.mapping.keys() if name.startswith("x")
        ]
        self.sliders = []
        for idx, settable in enumerate(settables):
            m_sec_property, slider = self.generate_m_section(
                dataset[settable].long_name, idx * 2 + 2, dataset[settable]
            )
            self.plot_data_mgr += m_sec_property
            self.sliders += [slider]

        m_sec_property, slider = self.generate_m_section(
            m_name, len(settables) * 2 + 4, self.dataset[y_param], parent=True
        )
        self.plot_data_mgr += m_sec_property
        self.sliders += [slider]

        self.plot_data_mgr.set_children()

        self.title_layout = QtWidgets.QHBoxLayout()
        self.title_layout.addWidget(self.sp)
        self.title_layout.addWidget(self.m_param_1_title)
        if self.cb_hist is not None:
            self.title_layout.addWidget(self.cb_hist)
        self.addLayout(self.title_layout)

        self.addLayout(self.local_parent)
        for i in self.sliders:
            self.addLayout(i)

    def cb_callback(self, checkbox, prop):
        setattr(self.plot_data_mgr, prop, checkbox.isChecked())
        self.plot_data_mgr.update()

    def generate_header(self, m_name):
        header_slc = QtWidgets.QLabel(self.geom_parent)
        header_slc.setMaximumSize(QtCore.QSize(40, 16777215))
        header_slc.setObjectName(m_name + "header_slc")

        header_avg = QtWidgets.QLabel(self.geom_parent)
        header_avg.setMaximumSize(QtCore.QSize(40, 16777215))
        header_avg.setObjectName(m_name + "header_avg")

        header_log = QtWidgets.QLabel(self.geom_parent)
        header_log.setMaximumSize(QtCore.QSize(40, 16777215))
        header_log.setObjectName(m_name + "header_log")

        header_letter = QtWidgets.QLabel(self.geom_parent)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(header_letter.sizePolicy().hasHeightForWidth())
        header_letter.setSizePolicy(sizePolicy)
        header_letter.setMinimumSize(QtCore.QSize(0, 0))
        header_letter.setMaximumSize(QtCore.QSize(10, 16777215))
        header_letter.setObjectName(m_name + "header_letter")

        header_name = QtWidgets.QLabel(self.geom_parent)
        header_name.setMaximumSize(QtCore.QSize(180, 16777215))
        header_name.setObjectName(m_name + "header_name")

        self.add_v_lines(m_name, 0)
        self.add_h_lines(m_name)
        self.local_parent.addWidget(header_letter, 0, 0, 1, 1)
        self.local_parent.addWidget(header_name, 0, 2, 1, 1)
        self.local_parent.addWidget(header_avg, 0, 4, 1, 1)
        self.local_parent.addWidget(header_slc, 0, 5, 1, 1)
        self.local_parent.addWidget(header_log, 0, 6, 1, 1)

        _translate = QtCore.QCoreApplication.translate
        header_slc.setText(_translate("MainWindow", "SLC"))
        header_log.setText(_translate("MainWindow", "log"))
        header_avg.setText(_translate("MainWindow", "AVG"))
        header_letter.setText(_translate("MainWindow", " "))
        header_name.setText(_translate("MainWindow", "name"))

    def generate_m_section(self, m_name, level, param, parent=False):
        letter = QtWidgets.QLabel(self.geom_parent)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(letter.sizePolicy().hasHeightForWidth())
        letter.setSizePolicy(sizePolicy)
        letter.setObjectName(m_name + "letter_{}".format(level))

        name = QtWidgets.QLabel(self.geom_parent)
        name.setMaximumSize(QtCore.QSize(250, 16777215))
        name.setObjectName(m_name + "name_{}".format(level))

        avg = QtWidgets.QCheckBox(self.geom_parent)
        avg.setText("")
        avg.setObjectName(m_name + "avg_{}".format(level))

        slc = QtWidgets.QCheckBox(self.geom_parent)
        slc.setText("")
        slc.setObjectName(m_name + "check_{}".format(level))

        log = QtWidgets.QCheckBox(self.geom_parent)
        log.setText("")
        log.setObjectName(m_name + "x_log_{}".format(level))

        _translate = QtCore.QCoreApplication.translate
        letter.setText(_translate("MainWindow", param.name))
        name.setText(
            _translate(
                "MainWindow",
                "{} ({})".format(param.attrs["long_name"], param.attrs["units"]),
            )
        )

        self.local_parent.addWidget(letter, level, 0, 1, 1)
        self.local_parent.addWidget(name, level, 2, 1, 1)
        self.local_parent.addWidget(avg, level, 4, 1, 1)
        self.local_parent.addWidget(slc, level, 5, 1, 1)
        self.local_parent.addWidget(log, level, 6, 1, 1)

        self.add_v_lines(m_name, level)

        slider = slider_mgr(param.name, param, self.geom_parent)

        if parent:
            avg.hide()
            slc.hide()

        m_param_set_prop = n_th_dimension_prop(
            param.name,
            "{} ({})".format(param.long_name, param.attrs["units"]),
            avg,
            slc,
            log,
            slider,
        )

        return m_param_set_prop, slider.hbox

    def add_h_lines(self, m_name):
        l1 = self.generate_h_line(m_name + "h_line_1")
        l2 = self.generate_h_line(m_name + "h_line_2")
        l3 = self.generate_h_line(m_name + "h_line_3")
        l4 = self.generate_h_line(m_name + "h_line_4")
        l5 = self.generate_h_line(m_name + "h_line_5")
        l6 = self.generate_h_line(m_name + "h_line_6")

        self.local_parent.addWidget(l1, 1, 0, 1, 1)
        self.local_parent.addWidget(l2, 1, 1, 1, 1)
        self.local_parent.addWidget(l3, 1, 2, 1, 1)
        self.local_parent.addWidget(l4, 1, 4, 1, 1)
        self.local_parent.addWidget(l5, 1, 5, 1, 1)
        self.local_parent.addWidget(l6, 1, 6, 1, 1)

    def add_v_lines(self, m_name, level):
        l1 = self.generate_v_line(m_name + "v_line_{}1".format(level))
        l2 = self.generate_v_line(m_name + "v_line_{}1".format(level))
        self.local_parent.addWidget(l1, level, 1, 1, 1)
        self.local_parent.addWidget(l2, level, 3, 1, 1)

    def generate_v_line(self, name):
        line = QtWidgets.QFrame(self.geom_parent)
        line.setFrameShape(QtWidgets.QFrame.VLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setObjectName(name)
        return line

    def generate_h_line(self, name):
        line = QtWidgets.QFrame(self.geom_parent)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setObjectName(name)
        return line
