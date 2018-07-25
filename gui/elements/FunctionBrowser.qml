import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtGraphicalEffects 1.0
import QtQuick.Controls.Styles 1.4

// Device function browser
Rectangle {
  id: popup
  property var target: "none"
  objectName: "Popup"
  width: 250
  parent: sidebar
  height: parent.height
  x: parent.width
  color:  "#3a4055"
  visible: false
  anchors.top: parent.top
  opacity: 0.85

  Column {
  anchors.left: parent.left
  anchors.right: parent.right
  spacing: 10
  // Header
  Text {
      id: browser_header
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.leftMargin: 30
      anchors.rightMargin: 30
      //text: "functions"
      text: parent.parent.target
      font.family: "Agency FB"
      font.weight: Font.Bold
      font.pointSize: 30
      x: 30
      color: "white"
  }

  // Function selector
  ComboBox {
   textRole: "name"
   anchors.left: parent.left
   anchors.right: parent.right
   anchors.leftMargin: 30
   anchors.rightMargin: 30
   opacity: 1
   model: ListModel {
           objectName: "Model"
           id: function_model
       }
   onCurrentIndexChanged: {
       if (typeof function_model.get(currentIndex) != 'undefined') {
          sidebar.device._list_args(function_model.get(currentIndex).device, function_model.get(currentIndex).name)
       }
   }
  }

  // Docs
  Text {
      id: docs_text
      text: ""
      wrapMode: "WordWrap"

      anchors.left: parent.left
      anchors.leftMargin: 30
      anchors.right: parent.right
      anchors.rightMargin:30

      font.family: "Agency FB"
      font.weight: Font.Bold
      font.pointSize: 14
      x: 30
      color: "white"

  }

  Text {
      id: args_label
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.leftMargin: 30
      anchors.rightMargin: 30
      text: "args"
      font.family: "Agency FB"
      font.weight: Font.Bold
      font.pointSize: 16
      x: 30
      color: "white"
  }

  ListView{
   visible: true
   id: executor_list
   //anchors.top: parent.top
   //anchors.topMargin: 100
   anchors.left: parent.left
   anchors.right: parent.right
   anchors.leftMargin: 30
   anchors.rightMargin: 30
   //opacity: 1
   model: executor_model
   height: popup.height
   width: popup.width
   delegate: Row {
     spacing: 10
     Text {
       text: name
       font.family: "Agency FB"
       font.pointSize: 14
       color: "white"

         }
       TextEdit {
           text: value
           font.family: "Agency FB"
           font.pointSize: 14
           color: "white"
           selectByMouse: true

             }
       }
     }

  }
  ListModel {
    objectName: "executor_model"
    id: executor_model

    ListElement {name:"default"
                 value:"default"
                 }
 }

  // Header


  function append(newElement) {
      function_model.append(newElement)
  }

  function clear() {
      function_model.clear()
  }


  function append_args(newElement) {
      executor_model.append(newElement)
  }

  function clear_args() {
      executor_model.clear()
  }

  // Documentation
  function set_docs(docs) {
   docs_text.text = docs.text
  }
}
