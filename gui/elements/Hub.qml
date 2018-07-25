import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtGraphicalEffects 1.0
import QtQuick.Controls.Styles 1.4

import QtQuick 2.5

Item {
    property var name
    property var x_pos
    property var y_pos
    property var device
    anchors.fill: parent
    
    // clickable element
    Clickable {
        objectName: "Clickable"
        text: parent.name
        x: parent.x_pos*parent.parent.width+100
        y: parent.y_pos*parent.parent.height
    }
    
    function append(newElement) {
        model.append(newElement)
    }
    
    // model
    ListModel {
        objectName: "Model"
        id: model
    }
        
    // sidebar
    Sidebar {
        device: parent.device
        objectName: "Sidebar"
        id: sidebar
        name: parent.name
        model: model
        footer: ""

    }    
}