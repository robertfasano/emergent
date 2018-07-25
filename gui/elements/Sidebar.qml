import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtGraphicalEffects 1.0
import QtQuick.Controls.Styles 1.4

Rectangle {
    id: sidebar
    anchors.top: parent.top
    anchors.topMargin: 0
    width: 350
    height: parent.height
    color:  "#3a4055"
    property string name
    property ListModel model
    property ListModel buttonModel
    property string footer
    property var device

    visible: parent.parent.element == name ? true: false

    // Header
    Text {
        id: sidebar_header_text
        text: parent.name
        font.family: "Agency FB"
        font.weight: Font.Bold
        font.pointSize: 42
        x: 30
        color: "white"
    }

    function change_value (name, value) {
        objectName: "changeValueFunction"
        for (var i=0; i<list_menu.count; i++) {
            if (list_menu.model.get(i).name == name) {
                list_menu.model.setProperty(i, "value", value)
            }

        }
    }

    property var popup: FunctionBrowser{id:popup}
    DeviceBrowser {id:list_menu}
    property var optimizer: Optimizer{id:optimizer}

    // Optimizer button
    Button{
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.bottomMargin: 20
        anchors.rightMargin: 20
        Layout.preferredWidth: (list_menu.parent.width-2*list_menu.anchors.leftMargin)/6
        y: 5
        iconSource: "../media/Material/bullseye-arrow.svg"

        onClicked: {
            parent.device._list_methods(name)
            parent.popup.visible = false
            if (parent.optimizer.visible == false) {
                parent.optimizer.visible = true
                parent.optimizer.target = name
            }
            else if (parent.optimizer.target == name) {
              parent.optimizer.visible = false
              }
            else {
              parent.optimizer.target = name
            }
        }
    }

    // Footer
    Text {
        id: sidebar_footer
        //anchors.bottom: parent.bottom
        //anchors.bottomMargin: 20
        text: parent.footer
        font.family: "Agency FB"
        font.pointSize: 14
        x: 30
        width: 200
        wrapMode: Text.WordWrap
        color: "white"

    }

}
