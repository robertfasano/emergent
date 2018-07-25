import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtGraphicalEffects 1.0
import QtQuick.Controls.Styles 1.4

// Device and parameter list
ListView {
    //anchors.fill: parent
    objectName: "list_menu"
    anchors.top: parent.top
    anchors.topMargin: 65
    anchors.left: parent.left
    anchors.leftMargin: 30
    id: list_menu
    //width: 250
    height: parent.height
    spacing:3
    model: parent.model
    property var popup: false

    delegate: RowLayout {
        spacing: 0
        Label {
            Layout.preferredWidth: (list_menu.parent.width-2*list_menu.anchors.leftMargin)/3
            font.family: "Agency FB"
            font.pointSize: value < -1110? 18: 16
            color: "white"
            font.underline: value < -1110? true: false
            text: value < -1110 ? name: name + ": "
            font.weight: value < -1110 ? Font.Bold: Font.Thin
        }
        TextEdit{
            Layout.preferredWidth: (list_menu.parent.width-2*list_menu.anchors.leftMargin)/3
            font.family: "Agency FB"
            font.pointSize: value < -1110? 18: 16
            color: "white"
            text: value < -1110? " ":value
            Keys.onReturnPressed: {
                sidebar.device._set_param(name, text, device)
            }
        }

        // Refresh button
        Button{
            Layout.preferredWidth: (list_menu.parent.width-2*list_menu.anchors.leftMargin)/6
            visible: value < -1110? true: false
            y: 5
            iconSource: "../media/Material/refresh.svg"
            onClicked:
                sidebar.device._refresh(name)
            //color: "#3a4055"
        }

        // Function browser button
        Button{
            Layout.preferredWidth: (list_menu.parent.width-2*list_menu.anchors.leftMargin)/6
            visible: value < -1110? true: false
            y: 5
            iconSource: "../media/Material/menu.svg"

            onClicked: {
                sidebar.optimizer.visible = false
                sidebar.device._list_methods(name)
                if (sidebar.popup.visible == false) {
                    sidebar.popup.visible = true
                    sidebar.popup.target = name
                }
                else if (sidebar.popup.target == name) {
                  sidebar.popup.visible = false
                  }
                else {
                  sidebar.popup.target = name
                }
            }
        }
    }
}
