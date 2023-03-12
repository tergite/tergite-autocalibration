import QtQuick 2.4
import QtGraphicalEffects 1.0
import QtQuick.Controls 1.6
import QtQuick.Dialogs.qml 1.0
import QtQuick.Controls.Styles.Desktop 1.0
import QtQuick.Layouts 1.3
import QtQuick.Window 2.10

import QtQuick.Layouts 1.12
import QtQuick.Controls 2.12
import QtQuick.Controls.Styles 1.4
import QtQuick.Window 2.12
import QtQuick.Controls.Material 2.12
import QtQuick.Shapes 1.12

ApplicationWindow {
    title: "Data Browser"
    width: 1600
    height: 800
    visible: true
    Material.theme: Material.Light

    TabBar {
        id : tabBar_databrowser
        height: 50
        anchors.left: parent.left
        anchors.leftMargin: 0
        anchors.right: parent.right
        anchors.rightMargin: 0
        anchors.top: parent.top
        anchors.topMargin: 0

        TabButton {
            text: qsTr("Overview")
            anchors.top: parent.top
            anchors.topMargin: 0
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 0
        }

        TabButton {
            text: qsTr("Search")
            anchors.top: parent.top
            anchors.topMargin: 0
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 0
        }
    }

    StackLayout {
        id: stackLayout
        currentIndex: tabBar_databrowser.currentIndex
        anchors.right: parent.right
        anchors.left: parent.left
        anchors.bottom: measurement_overview_state_info.top
        anchors.top: tabBar_databrowser.bottom

        Item {
            ColumnLayout {
                id: overview_tab_col_layout
                anchors.fill: parent
                transformOrigin: Item.TopLeft

                RowLayout {
                    id: measurement_overview_layout
                    Rectangle {
                        color: "#FFFFFFFF"
                        Layout.fillHeight: true
                        Layout.leftMargin: 10
                        Layout.rightMargin: 10
                        width : 180
                        radius : 5

                        ListView {
                            Component {
                                id : date_list_delegate
                                Item {
                                    width: parent.width
                                    height: 36

                                    Rectangle {
                                        id: r
                                        width: parent.width-20
                                        x: 10
                                        height: 36
                                        radius : 5
                                        color: 'transparent'

                                        RowLayout {
                                            width: 100
                                            height: 34
                                            spacing : 10
                                            Rectangle {
                                                id : rec_ind
                                                width: 12
                                                radius : 5
                                                height : 34
                                                color: "transparent"
                                                Layout.fillHeight: true
                                            }

                                            Text {
                                                text: date
                                                Layout.alignment: Qt.AlignHLeft | Qt.AlignVCenter
                                                Layout.fillHeight: false
                                                font.pixelSize: 16
                                            }

                                        }
                                    }

                                    Rectangle {
                                        y : 36
                                        width: parent.width
                                        height: 5
                                        color: "transparent"
                                    }

                                    function hover_in() {
                                        if (date_list_view.currentIndex != index) {
                                            r.color = "#FAFAFA"
                                            rec_ind.color = "#F8BBD0"
                                        }
                                    }
                                    function hover_out() {
                                        if (date_list_view.currentIndex != index) {
                                            r.color = "transparent"
                                            rec_ind.color = "transparent"
                                        }
                                    }

                                    function my_click() {
                                        r.color = "transparent"
                                        rec_ind.color = "transparent"
                                        date_list_view.currentIndex = index;
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: {
                                            my_click(); focus=true
                                        }
                                        onEntered: hover_in()
                                        onExited: hover_out()
                                    }
                                }
                            }

                            Component {
                                id: date_list_highlight

                                Rectangle {
                                    id : date_list_highlight_box
                                    height: 0
                                    color: "transparent"
                                    width: measurement_overview_layout.width
                                    x: 10

                                    RowLayout {
                                        height: 36
                                        Rectangle {
                                            x : 10
                                            width: 12
                                            radius : 5
                                            color: Material.color(Material.Pink)
                                            Layout.fillHeight: true
                                        }
                                        Rectangle {
                                            width: 210
                                            radius : 5
                                            color: "#F5F5F5"
                                            Layout.fillHeight: true
                                        }
                                        spacing : 0
                                    }
                                }
                            }

                            Component {
                                id : date_list_header

                                Rectangle {
                                    id: header_car
                                    color: "#FFFFFF"

                                    width: parent.width
                                    height : 40 + 20
                                    radius : 5

                                    Rectangle {
                                        id: header
                                        width: parent.width-10
                                        height: 40
                                        x : 10
                                        y : 10

                                        radius : 5
                                        color: "#8e24aa"

                                        Text {
                                            width: parent.width
                                            height: 30
                                            color : "#FFFFFF"
                                            text: qsTr("Date")
                                            anchors.leftMargin: 25
                                            anchors.fill: parent
                                            verticalAlignment: Text.AlignVCenter
                                            horizontalAlignment: Text.AlignLeft
                                            font.bold: true
                                            font.pixelSize: 16
                                        }
                                        MouseArea {
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            onEntered: header.color= "#9C27B0"
                                            onExited: header.color= "#8e24aa"
                                        }
                                    }
                                }
                            }
                            objectName : 'date_list_view'
                            id: date_list_view
                            width: parent.width
                            height : parent.height
                            delegate: date_list_delegate
                            highlight: date_list_highlight
                            header : date_list_header
                            spacing : 10
                            clip : true
                            model: date_list_model
                            onCurrentItemChanged: signal_handler.update_date_selection(date_list_view.currentIndex)
                        }
                    }

                    Rectangle {
                        color: "#FFFFFFFF"

                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.rightMargin: 10
                        radius : 5

                        ListView {
                            id: data_content_view
                            height : parent.height
                            width : parent.width
                            spacing: 10
                            clip : true

                            Component {
                                id : data_content_view_delegate

                                Rectangle {
                                    id: row_overview
                                    height: 36
                                    width: data_content_view.width

                                    color: "#F5F5F5"
                                    radius : 5
                                    RowLayout {
                                        id: rowLayout115
                                        width: row_overview.width
                                        height: row_overview.height

                                        Rectangle {
                                            width : 20
                                            height : 20
                                            Layout.leftMargin : 15
                                            Layout.topMargin : 4
                                            color : 'transparent'
                                            Star_shape {
                                                anchors.fill: parent
                                                size : 20
                                                uuid_ : uuid
                                                selected : starred
                                            }
                                        }

                                        TextEdit {
                                            height: 36
                                            text: id_
                                            focus : true
                                            readOnly : true
                                            selectByMouse : true
                                            font.pixelSize: 15
                                            Layout.preferredWidth: 80
                                            Layout.leftMargin: 20
                                        }

                                        TextEdit {
                                            text: uuid
                                            focus : true
                                            readOnly : true
                                            selectByMouse : true
                                            font.pixelSize: 15
                                            Layout.preferredWidth: 200
                                        }

                                        Text {
                                            text: date
                                            font.pixelSize: 15
                                            Layout.preferredWidth: 100
                                        }

                                        Item {
                                            height: 36
                                            TextInput {
                                                id : text_field_measurment_overview
                                                z : 1
                                                y : (36-18)/2
                                                height: 40
                                                Layout.preferredWidth: text_field_measurment_overview.contentWidth
                                                font.pixelSize: 15
                                                text : name
                                                selectByMouse : true
                                                selectedTextColor : '#FFFFFF'
                                                selectionColor : '#EC407A'
                                                onEditingFinished : {
                                                    if (name != text_field_measurment_overview.text) {
                                                        signal_handler.update_name_meaurement(uuid,text_field_measurment_overview.text);
                                                    }
                                                }
                                            }
                                        }

                                        Item {
                                            id: element31
                                            width: 200
                                            height: 36
                                            Layout.fillWidth: true
                                        }

                                        Text {
                                            id: element32
                                            text: keywords
                                            Layout.rightMargin: 20
                                            font.pixelSize: 15
                                        }
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onEntered: row_overview.color= "#EEEEEE"
                                        onExited: row_overview.color= "#F5F5F5"
                                        onDoubleClicked : signal_handler.plot_ds_qml(uuid);
                                        onClicked : focus = true;
                                        z : -1
                                    }
                                }

                            }

                            Component {
                                id : data_content_view_header
                                Rectangle {
                                    anchors.right: parent.right
                                    anchors.left: parent.left

                                    height : 40+20

                                    Rectangle {
                                        id: data_content_view_header_box
                                        height: 40

                                        color: "#8E24AA"
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.top: parent.top
                                        anchors.topMargin: 10
                                        radius : 5
                                        RowLayout {
                                            id: rowLayout
                                            width: data_content_view_header_box.width
                                            height: data_content_view_header_box.height

                                            Rectangle {
                                                width : 20
                                                height : 20
                                                Layout.leftMargin : 15
                                                Layout.topMargin : 4
                                                color : 'transparent'
                                                Star_shape {
                                                    anchors.fill: parent
                                                    size : 20
                                                }
                                            }

                                            Text {
                                                text: qsTr("ID")
                                                color : 'white'
                                                Layout.leftMargin: 20
                                                Layout.preferredWidth: 80
                                                font.bold: true
                                                font.pixelSize: 16
                                            }

                                            Text {
                                                text: qsTr("UUID")
                                                color : 'white'
                                                Layout.preferredWidth: 200
                                                font.bold: true
                                                font.pixelSize: 16
                                            }


                                            Text {
                                                text: qsTr("Time")
                                                color : 'white'
                                                Layout.preferredWidth: 100
                                                Layout.fillWidth: false
                                                font.bold: true
                                                font.pixelSize: 16
                                            }

                                            Text {
                                                text: qsTr("Name")
                                                color : 'white'
                                                font.bold: true
                                                font.pixelSize: 16
                                            }


                                            Item {
                                                width: 200
                                                height: data_content_view_header_box.height
                                                Layout.fillWidth: true
                                            }

                                            Text {
                                                text: qsTr("Keywords")
                                                color : 'white'
                                                Layout.rightMargin: 20
                                                font.bold: true
                                                font.pixelSize: 16
                                            }

                                        }

                                        MouseArea {
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            onEntered: data_content_view_header_box.color= "#9C27B0"
                                            onExited: data_content_view_header_box.color= "#8e24aa"
                                        }
                                    }
                                }
                            }

                            delegate: data_content_view_delegate
                            header : data_content_view_header
                            model:data_content_view_model

                            flickableDirection: Flickable.VerticalFlick
                            boundsBehavior: Flickable.StopAtBounds

                            ScrollBar.vertical: ScrollBar {}
                        }
                    }
                }


            }
        }

        Item {
            id: search_tab
            Layout.fillHeight: true
            Layout.fillWidth: true

            TextField {
                id: textField
                height: 80
                anchors.right: parent.right
                anchors.rightMargin: 15
                anchors.left: parent.left
                anchors.leftMargin: 15
                anchors.top: parent.top
                anchors.topMargin: 10
                font.pointSize: 20
                placeholderText: qsTr("P1, P2 FROM 12/10/2020 SORT DATE")
            }

            Rectangle {
                color: "#FFFFFFFF"

                y : 100
                width : parent.width
                height : parent.height - 100
                Layout.rightMargin: 10
                radius : 5

                ListView {
                    Component {
                        id : data_content_search_view_delegate

                        Rectangle {
                            id: row_overview
                            height: 42

                            color: "#F5F5F5"
                            anchors.right: parent.right
                            anchors.left: parent.left
                            anchors.rightMargin: 10
                            anchors.leftMargin: 10
                            radius : 5
                            RowLayout {
                                id: rowLayout115
                                width: row_overview.width
                                height: row_overview.height

                                Rectangle {
                                    width : 20
                                    height : 20
                                    Layout.leftMargin : 15
                                    Layout.topMargin : (42-20)/4
                                    color : 'transparent'
                                    Star_shape {
                                        anchors.fill: parent
                                        size : 20
                                        uuid_ : uuid
                                    }

                                }

                                Text {
                                    id: element19
                                    height: 42
                                    text: id_
                                    font.pixelSize: 16
                                    Layout.preferredWidth: 80
                                    Layout.leftMargin: 20
                                }

                                Text {
                                    id: element28
                                    text: uuid
                                    font.pixelSize: 16
                                    Layout.preferredWidth: 200
                                }

                                Text {
                                    id: element29
                                    text: date
                                    Layout.fillWidth: false
                                    font.pixelSize: 16
                                    Layout.preferredWidth: 230
                                }

                                Text {
                                    id: element30
                                    text: name
                                    font.pixelSize: 16
                                }

                                Item {
                                    id: element31
                                    width: 200
                                    height: 42
                                    Layout.fillWidth: true
                                }

                                Text {
                                    id: element32
                                    text: keywords
                                    Layout.rightMargin: 20
                                    font.pixelSize: 16
                                }
                            }
                        }

                    }

                    Component {
                        id : data_content_search_view_header
                        Rectangle {
                            anchors.right: parent.right
                            anchors.left: parent.left

                            height : 64+20

                            Rectangle {
                                id: data_content_search_view_header_box
                                height: 64

                                color: "#8E24AA"
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.topMargin: 10
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                radius : 5
                                RowLayout {
                                    id: rowLayout
                                    width: data_content_search_view_header_box.width
                                    height: data_content_search_view_header_box.height

                                    Rectangle {
                                        width : 20
                                        height : 20
                                        Layout.leftMargin : 15
                                        Layout.topMargin : (42-20)/4
                                        color : 'transparent'
                                        Star_shape {
                                            anchors.fill: parent
                                            size : 20

                                        }
                                    }

                                    Text {
                                        text: qsTr("ID")
                                        color : 'white'
                                        Layout.leftMargin: 20
                                        Layout.preferredWidth: 40
                                        font.pixelSize: 22
                                    }

                                    Text {
                                        text: qsTr("TUID")
                                        color : 'white'
                                        Layout.preferredWidth: 240
                                        font.pixelSize: 22
                                    }


                                    Text {
                                        text: qsTr("Date")
                                        color : 'white'
                                        Layout.preferredWidth: 230
                                        Layout.fillWidth: false
                                        font.pixelSize: 22
                                    }

                                    Text {
                                        text: qsTr("Name")
                                        color : 'white'
                                        font.pixelSize: 22
                                    }


                                    Item {
                                        width: 200
                                        height: data_content_search_view_header_box.height
                                        Layout.fillWidth: true
                                    }

                                    Text {
                                        text: qsTr("Keywords")
                                        color : 'white'
                                        Layout.rightMargin: 20
                                        font.pixelSize: 22
                                    }

                                }
                            }
                        }
                    }

                    id: data_content_search_search_view
                    height : parent.height
                    width : parent.width
                    spacing: 10
                    clip : true

                    delegate: data_content_search_view_delegate
                    // highlight: data_content_search_view_highlight
                    header : data_content_search_view_header

                    model:ListModel {
                        ListElement {
                            id_: "100"
                            uuid: "12354568912345"
                            date: "20/11/2020 15:12"
                            name: "1D scan"
                            keywords: "frequency, spin probability Q1"
                        }

                        ListElement {
                            id_: "101"
                            uuid: "12354568912345"
                            date: "20/11/2020 15:23"
                            name: "SD2 calibration"
                            keywords: "vSD2_P, vP4, SD response"
                        }

                        ListElement {
                            id_: "102"
                            uuid: "12354568912345"
                            date: "20/11/2020"
                            name: "2D scan"
                            keywords: "frequency, MW power, spin probability Q1, spin probability Q"
                        }

                        ListElement {
                            id_: "103"
                            uuid: "12354568912345"
                            date: "20/11/2020"
                            name: "1D scan"
                            keywords: "frequency, spin probability Q1"
                        }
                    }




                }
            }


        }

    }

    RowLayout {
        id: measurement_overview_state_info
        height: 50

        anchors.right: parent.right
        anchors.left: parent.left
        anchors.bottom: parent.bottom

        Item {
            Layout.fillWidth: true
        }

        SwitchDelegate {
            objectName : 'enable_liveplotting'
            id: enable_liveplotting
            height: 50
            text: qsTr("Enable liveplotting")
            Layout.preferredWidth: 250
            checked: true
            onToggled : signal_handler.enable_liveplotting(enable_liveplotting.checked);
        }
    }

    MouseArea {
        anchors.fill: parent
        onClicked: focus = true
        z : -5
    }

}