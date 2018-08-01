import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtGraphicalEffects 1.0
import "elements" as Elements

ApplicationWindow {
    visible: true
    width: 1280
    height: 720
    title: qsTr("EMERGENT")
    color: "white"
    objectName: "applicationWindow"

    // Nested tree of nodes
    Item {
        ListView {
            id: list
            anchors.fill: parent
            model: nestedModel
            delegate: categoryDelegate

        }

        ListModel {
            id: nestedModel
        }
    }

}
