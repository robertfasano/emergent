import QtQuick 2.5

Text {
    objectName: "text"
    text: "text"
    font.family: "Agency FB"
    font.pointSize: 18
    font.weight: parent.parent.element == text ? Font.Bold: Font.Thin
    color: "#3a4055"
    focus: false
    
    property var connected: 0
    visible: connected? true: false
    
    MouseArea {
        objectName: "clickableMouseArea"
        anchors.fill: parent
        onClicked: {
            if (parent.parent.parent.element != parent.text) {
                parent.parent.parent.element = parent.text
                parent.focus = true
            }
            else  {
                menuMinimized.visible = true
                parent.focus = false
                parent.parent.parent.element = "none"

            }
        }
    }
}