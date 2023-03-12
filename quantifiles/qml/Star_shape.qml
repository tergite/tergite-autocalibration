import QtQuick 2.12
import QtQuick.Shapes 1.12

Item {
    id : star_shape
    property var size: 30
    property var ratio : 0.4
    property var angle_offset : Math.PI*2*3/20
    property var rot_angle : Math.PI*2/10
    property var selected : false
    property var linewidth : 1
    property var uuid_ : 0
    Shape {
        width: star_shape.size
        height: star_shape.size

        ShapePath {
            id : star_path
            strokeWidth: star_shape.linewidth
            strokeColor: (star_shape.selected == true) ? '#FBC02D' : '#9E9E9E' 
            fillColor: (star_shape.selected == true) ? '#FBC02D' : '#9E9E9E' 
            PathMove { x: star_shape.size/2+ star_shape.size * Math.cos(star_shape.angle_offset+2*Math.PI*0/5)/2; y: star_shape.size/2 + star_shape.size * Math.sin(star_shape.angle_offset+2 * Math.PI*0/5)/2 }
            PathLine { x: star_shape.size/2+ star_shape.size * Math.cos(star_shape.angle_offset+2*Math.PI*0/5)/2; y: star_shape.size/2 + star_shape.size * Math.sin(star_shape.angle_offset+2 * Math.PI*0/5)/2 }
            PathLine { x: star_shape.size/2+ star_shape.size * Math.cos(star_shape.angle_offset+2*Math.PI*0/5+star_shape.rot_angle)/2*star_shape.ratio ;
                y: star_shape.size/2 + star_shape.size * Math.sin(star_shape.angle_offset+2 * Math.PI*0/5+star_shape.rot_angle)/2*star_shape.ratio }
            PathLine { x: star_shape.size/2+ star_shape.size * Math.cos(star_shape.angle_offset+2*Math.PI*1/5)/2; y: star_shape.size/2 + star_shape.size * Math.sin(star_shape.angle_offset+2 * Math.PI*1/5)/2 }
            PathLine { x: star_shape.size/2+ star_shape.size * Math.cos(star_shape.angle_offset+2*Math.PI*1/5+star_shape.rot_angle)/2*star_shape.ratio ;
                y: star_shape.size/2 + star_shape.size * Math.sin(star_shape.angle_offset+2 * Math.PI*1/5+star_shape.rot_angle)/2*star_shape.ratio }
            PathLine { x: star_shape.size/2+ star_shape.size * Math.cos(star_shape.angle_offset+2*Math.PI*2/5)/2; y: star_shape.size/2 + star_shape.size * Math.sin(star_shape.angle_offset+2 * Math.PI*2/5)/2 }
            PathLine { x: star_shape.size/2+ star_shape.size * Math.cos(star_shape.angle_offset+2*Math.PI*2/5+star_shape.rot_angle)/2*star_shape.ratio ;
                y: star_shape.size/2 + star_shape.size * Math.sin(star_shape.angle_offset+2 * Math.PI*2/5+star_shape.rot_angle)/2*star_shape.ratio }
            PathLine { x: star_shape.size/2+ star_shape.size * Math.cos(star_shape.angle_offset+2*Math.PI*3/5)/2; y: star_shape.size/2 + star_shape.size * Math.sin(star_shape.angle_offset+2 * Math.PI*3/5)/2 }
            PathLine { x: star_shape.size/2+ star_shape.size * Math.cos(star_shape.angle_offset+2*Math.PI*3/5+star_shape.rot_angle)/2*star_shape.ratio ;
                y: star_shape.size/2 + star_shape.size * Math.sin(star_shape.angle_offset+2 * Math.PI*3/5+star_shape.rot_angle)/2*star_shape.ratio }
            PathLine { x: star_shape.size/2+ star_shape.size * Math.cos(star_shape.angle_offset+2*Math.PI*4/5)/2; y: star_shape.size/2 + star_shape.size * Math.sin(star_shape.angle_offset+2 * Math.PI*4/5)/2 }
            PathLine { x: star_shape.size/2+ star_shape.size * Math.cos(star_shape.angle_offset+2*Math.PI*4/5+star_shape.rot_angle)/2*star_shape.ratio ;
                y: star_shape.size/2 + star_shape.size * Math.sin(star_shape.angle_offset+2 * Math.PI*4/5+star_shape.rot_angle)/2*star_shape.ratio }
            PathLine { x: star_shape.size/2+ star_shape.size * Math.cos(star_shape.angle_offset+2*Math.PI*0/5)/2; y: star_shape.size/2 + star_shape.size * Math.sin(star_shape.angle_offset+2 * Math.PI*0/5)/2 }

        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onClicked: {
                star_shape.selected = (star_shape.selected == true) ? false : true;
                signal_handler.star_measurement(uuid_, star_shape.selected);
                }
            z : 1
        }

    }
}