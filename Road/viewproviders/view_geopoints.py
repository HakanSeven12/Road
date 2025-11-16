# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Cluster objects."""

import FreeCAD, FreeCADGui
from pivy import coin
from .view_geo_object import ViewProviderGeoObject
import math


class ViewProviderGeoPoints(ViewProviderGeoObject):
    """This class is about Cluster Object view features."""

    def __init__(self, vobj):
        """Set view properties."""
        super().__init__(vobj, "GeoPoint")

        vobj.addProperty(
            "App::PropertyEnumeration", "MarkerType", "Marker Style",
            "Justification of point labels").MarkerType = ["Point", "Plus", "Cross", "Line", "None"]

        vobj.addProperty(
            "App::PropertyEnumeration", "MarkerFrame", "Marker Style",
            "Justification of point labels").MarkerFrame = ["Circle", "Square", "None"]

        vobj.addProperty(
            "App::PropertyColor", "MarkerColor", "Marker Style",
            "Color of point marker").MarkerColor = (1.0, 1.0, 1.0)

        vobj.addProperty(
            "App::PropertyBool", "Number", "Labels Visibility",
            "Show/hide number label").Number = True

        vobj.addProperty(
            "App::PropertyBool", "Name", "Labels Visibility",
            "Show/hide name label").Name = False

        vobj.addProperty(
            "App::PropertyBool", "Easting", "Labels Visibility",
            "Show/hide easting label").Easting = False

        vobj.addProperty(
            "App::PropertyBool", "Northing", "Labels Visibility",
            "Show/hide norting label").Northing = False

        vobj.addProperty(
            "App::PropertyBool", "Elevation", "Labels Visibility",
            "Show/hide elevation label").Elevation = True

        vobj.addProperty(
            "App::PropertyBool", "Description", "Labels Visibility",
            "Show/hide description label").Description = False

        vobj.addProperty(
            "App::PropertyColor", "LabelColor", "Label Style",
            "Color of point labels").LabelColor = (1.0, 1.0, 1.0)

        vobj.addProperty(
            "App::PropertyFloat", "LabelSize", "Label Style",
            "Size of point labels").LabelSize = 10

        vobj.addProperty(
            "App::PropertyFont", "FontName", "Label Style",
            "Font name of point labels").FontName

        vobj.addProperty(
            "App::PropertyEnumeration", "Justification", "Label Placement",
            "Justification of point labels").Justification = ["Left", "Center", "Right"]

        vobj.addProperty(
            "App::PropertyFloat", "LineSpacing", "Label Placement",
            "Line spacing between point labels").LineSpacing = 1

        vobj.addProperty(
            "App::PropertyPlacement", "LabelOffset", "Label Placement",
            "Placement").LabelOffset = FreeCAD.Placement()

        vobj.addProperty(
            "App::PropertyPythonObject", "LabelDisplay", "Label Style", 
            "Keeper property for label visibilities").LabelDisplay = {
                "Number": vobj.Number,
                "Name": vobj.Name,
                "Easting": vobj.Easting,
                "Northing": vobj.Northing,
                "Elevation": vobj.Elevation,
                "Description": vobj.Description}

        vobj.Proxy = self
        vobj.PointSize = 10

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        super().attach(vobj)
        self.Object = vobj.Object

        #-------------------------------------------------------------
        # Marker
        #-------------------------------------------------------------

        self.marker_scale = coin.SoScale()
        self.marker_color = coin.SoBaseColor()

        self.frame_coordinate = coin.SoCoordinate3()
        self.frame_line = coin.SoLineSet()
        
        self.frame = coin.SoSeparator()
        self.frame.addChild(self.frame_coordinate)
        self.frame.addChild(self.frame_line)

        self.vertices = coin.SoCoordinate3()
        self.line = coin.SoIndexedLineSet()

        # Create a hidden template for the marker geometry
        # This prevents the origin geometry from affecting bounding box
        marker_template = coin.SoSeparator()
        marker_template.addChild(self.marker_color)
        marker_template.addChild(self.marker_scale)
        marker_template.addChild(self.vertices)
        marker_template.addChild(self.line)
        marker_template.addChild(self.frame)

        self.marker_copy = coin.SoMultipleCopy()
        self.marker_copy.addChild(marker_template)

        #-------------------------------------------------------------
        # Labels
        #-------------------------------------------------------------

        self.label_color = coin.SoBaseColor()
        self.font = coin.SoFont()
        self.offset = coin.SoTranslation()
        self.label_data = coin.SoGroup()

        labels = coin.SoSeparator()
        labels.addChild(self.label_color)
        labels.addChild(self.font)
        labels.addChild(self.label_data)

        #-------------------------------------------------------------
        # Level of Detail
        #-------------------------------------------------------------

        level0 = coin.SoAnnotation()
        level0.addChild(self.marker_copy)
        level0.addChild(labels)

        level1 = coin.SoAnnotation()
        level1.addChild(self.marker_copy)

        level2 = coin.SoAnnotation()
        level2.addChild(self.marker_copy)

        lod = coin.SoLevelOfDetail()
        lod.addChild(level0)
        lod.addChild(level1)
        lod.addChild(level2)

        lod.screenArea.values = [100]

        #-------------------------------------------------------------
        # Point
        #-------------------------------------------------------------

        self.drag_group = coin.SoSeparator()
        self.coordinate = coin.SoCoordinate3()
        geometry = coin.SoPointSet()

        self.standard.addChild(self.drag_group)
        self.standard.addChild(self.coordinate)
        self.standard.addChild(geometry)
        self.standard.addChild(lod)

        #-------------------------------------------------------------
        # Initialize
        #-------------------------------------------------------------

        self.onChanged(vobj, "MarkerType")
        self.onChanged(vobj, "MarkerFrame")
        self.onChanged(vobj, "MarkerColor")
        self.onChanged(vobj, "PointSize")
        self.onChanged(vobj, "LabelDisplay")
        self.onChanged(vobj, "LabelOffset")
        self.onChanged(vobj, "LabelColor")
        self.onChanged(vobj, "LabelSize")
        self.onChanged(vobj, "FontName")
        self.onChanged(vobj, "Justification")
        self.onChanged(vobj, "LineSpacing")

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        super().updateData(obj, prop)

        if prop == "Points":
            points = obj.Points.Points
            self.coordinate.point.values = points
            self.label_data.removeAllChildren()

            matrices = []
            for i, pt in enumerate(points):
                matrix = coin.SbMatrix()
                matrix.setTransform(
                    coin.SbVec3f(pt), 
                    coin.SbRotation(), 
                    coin.SbVec3f(1.0, 1.0, 1.0))
                matrices.append(matrix)

                location = coin.SoTranslation()
                text = coin.SoAsciiText()

                label_set = []
                vobj = obj.ViewObject
                display = vobj.LabelDisplay
                no = list(obj.Model.keys())[i]
                data = list(obj.Model.values())[i]
                for label, show in display.items():
                    if not show: continue

                    if label == "Number": 
                        label_set.append(no)
                    elif isinstance(data.get(label), float):
                        label_set.append(str(round(data.get(label), 3)))
                    else:
                        label_set.append(data.get(label))

                text.string.setValues(label_set)

                if vobj.Justification == "Left":
                    text.justification = coin.SoAsciiText.LEFT
                elif vobj.Justification == "Right":
                    text.justification = coin.SoAsciiText.RIGHT
                else:
                    text.justification = coin.SoAsciiText.CENTER
                
                text.spacing = vobj.LineSpacing
                location.translation = pt

                label = coin.SoTransformSeparator()
                label.addChild(location)
                label.addChild(text)

                level0 = coin.SoAnnotation()
                level0.addChild(label)

                level1 = coin.SoAnnotation()

                lod = coin.SoLevelOfDetail()
                lod.addChild(level0)
                lod.addChild(level1)

                lod.screenArea.values = [250]

                self.label_data.addChild(lod)

            self.marker_copy.matrix.values = matrices

    def onChanged(self, vobj, prop):
        """Update Object visuals when a view property changed."""
        if prop == "MarkerType":
            type = vobj.getPropertyByName(prop)
            horizontal = FreeCAD.Vector(1, 0, 0)
            vertical = FreeCAD.Vector(0, 1, 0)

            vertices=[]
            indices = []
            if type == "Point": 
                vertices = [FreeCAD.Vector()]

            elif type == "Plus": 
                vertices = [
                    vertical, 
                    vertical.negative(), 
                    horizontal, 
                    horizontal.negative()]

                indices = [0, 1, -1, 2, 3, -1]

            elif type == "Cross": 
                vertices = [
                    vertical.add(horizontal), 
                    vertical.negative().add(horizontal.negative()), 
                    vertical.negative().add(horizontal), 
                    vertical.add(horizontal.negative())]

                indices = [0, 1, -1, 2, 3, -1]

            elif type == "Line": 
                vertices = [
                    vertical.multiply(.5), 
                    FreeCAD.Vector()]

                indices = [0, 1, -1]
            
            self.vertices.point.values = vertices
            self.line.coordIndex.values = indices

        elif prop == "MarkerFrame":
            frame = vobj.getPropertyByName(prop)

            vertices=[]
            if frame == "Circle":
                radius = 0.5
                num_points = 16
                for i in range(num_points):
                    angle = math.radians((360 / num_points) * i)
                    x = radius * math.cos(angle)
                    y = radius * math.sin(angle)
                    vertices.append(FreeCAD.Vector(x, y))
                vertices.append(vertices[0])

            elif frame == "Square":
                horizontal = FreeCAD.Vector(0.5, 0, 0)
                vertical = FreeCAD.Vector(0, 0.5, 0)
                self.frame_coordinate.point.values = [
                    vertical.add(horizontal), 
                    vertical.add(horizontal.negative()), 
                    vertical.negative().add(horizontal.negative()), 
                    vertical.negative().add(horizontal), 
                    vertical.add(horizontal)]

            self.frame_coordinate.point.values = vertices

        elif prop == "MarkerColor":
            color = vobj.getPropertyByName(prop)
            self.marker_color.rgb = color[:3]

        elif prop == "PointSize":
            scale = vobj.PointSize * 100
            self.marker_scale.scaleFactor.setValue(scale, scale, 1)

        elif prop in ["Number", "Name", "Easting", "Northing", "Elevation", "Description"]:
            vobj.LabelDisplay[prop] = vobj.getPropertyByName(prop)
            self.onChanged(vobj, "LabelDisplay")

        elif prop == "LabelColor":
            color = vobj.getPropertyByName(prop)
            self.label_color.rgb = color[:3]

        elif prop == "LabelSize":
            self.font.size = vobj.getPropertyByName(prop) * 100

        elif prop == "FontName":
            self.font.name = vobj.getPropertyByName(prop).encode("utf8")

        elif prop == "LabelOffset":
            self.offset.translation = vobj.LabelOffset.Base

        elif prop in ["Justification", "LineSpacing", "LabelDisplay"]:
            self.updateData(vobj.Object, "Points")

    def doubleClicked(self, vobj):
        """Detect double click"""
        dragger = coin.SoTranslate2Dragger()
        marker = coin.SoMarkerSet()
        scale = coin.SoScale()

        scale.scaleFactor.setValue(1000.0, 1000.0, 1000.0)
        dragger.translation.setValue(0, 0, 0)
        marker.markerIndex = 81

        translator = dragger.getPart("translator", False)
        geometry = translator.getChildren()[1]
        geometry.removeAllChildren()
        geometry.addChild(marker)

        self.drag_group.addChild(scale)
        self.drag_group.addChild(dragger)

        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.view.addDraggerCallback(dragger, "addMotionCallback", self.drag)
        self.view.addDraggerCallback(dragger, "addFinishCallback", self.drop)

        return True

    def drag(self, dragger):
        self.move.translation = dragger.translation

    def drop(self, dragger):
        displacement = FreeCAD.Vector(dragger.translation.getValue())
        self.Object.Placement.move(displacement)
        self.move.translation = FreeCAD.Vector()
        self.drag_group.removeAllChildren()
        FreeCAD.ActiveDocument.recompute()