import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtGraphicalEffects 1.0
import "elements" as Elements

ApplicationWindow {
    visible: true
    width: 1280
    height: 720
    title: qsTr("gMOT control")
    color: "white"
    objectName: "applicationWindow"

    // Experimental control
    Canvas{
        objectName: "canvas"
        id:  canvas
        width: parent.width
        height: parent.height
        Component.onCompleted: loadImage("media/background.png")
        onImageLoaded: requestPaint()
        onPaint: {
            var ctx = getContext("2d")
            var im = ctx.createImageData("media/background.png")
            ctx.drawImage(im,100,0, parent.width, parent.height)}

        property string element
        element: "none"

        // Menu bar
        Rectangle{
            objectName: "minimizedMenu"
            visible: parent.element == 'none' ? true: false
            id: menuMinimized
            anchors.top: parent.top
            anchors.topMargin: 0
            width: 100
            height: parent.height
            color:  "#3a4055"
        }

        Elements.Hub{
            name: "mot"
            objectName: "motHub"
            x_pos: 0.4865
            y_pos: 0.8
            device: mot
        }

        Elements.Hub{
            name: "autoAlign"
            objectName: "autoAlignHub"
            x_pos: 0.6
            y_pos: 0.2
            device: autoAlign
        }

        Elements.Hub{
            name: "dummy"
            objectName: "dummyHub"
            x_pos: 0.85
            y_pos: 0.025
            device: dummy
        }

        Image {
        source: "media/nist.png"
        x: 0.76*parent.width
        y: 0.92*parent.height
        width: 300
        height:50
        }

    }
}
