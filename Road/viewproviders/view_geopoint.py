# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2025 Hakan Seven <hakanseven12@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""Provides the viewprovider code for Cluster objects."""

import FreeCAD, FreeCADGui
from pivy import coin

import math

from ..variables import icons_path
from ..utils.get_group import georigin


class ViewProviderGeoPoint:
    """This class is about Cluster Object view features."""

    def __init__(self, vobj):
        """Set view properties."""
        vobj.addProperty(
            "App::PropertyEnumeration", "MarkerType", "Marker Style",
            "Justification of point labels").MarkerType = ["Point", "Empty", "Plus", "Cross", "Line"]

        vobj.addProperty(
            "App::PropertyBool", "CircleFrame", "Marker Style",
            "Show/hide number label").CircleFrame = True

        vobj.addProperty(
            "App::PropertyBool", "SquareFrame", "Marker Style",
            "Show/hide number label").SquareFrame = False

        vobj.addProperty(
            "App::PropertyColor", "MarkerColor", "Marker Style",
            "Color of point marker").MarkerColor = (1.0, 1.0, 1.0)

        vobj.addProperty(
            "App::PropertyFloat", "MarkerSize", "Marker Style",
            "Size of point marker").MarkerSize = 0.1

        vobj.addProperty(
            "App::PropertyBool", "Number", "Labels Visibility",
            "Show/hide number label").Number = True

        vobj.addProperty(
            "App::PropertyBool", "Label", "Labels Visibility",
            "Show/hide label").Label = False

        vobj.addProperty(
            "App::PropertyBool", "Easting", "Labels Visibility",
            "Show/hide easting label").Easting = False

        vobj.addProperty(
            "App::PropertyBool", "Northing", "Labels Visibility",
            "Show/hide norting label").Northing = False

        vobj.addProperty(
            "App::PropertyBool", "PointElevation", "Labels Visibility",
            "Show/hide elevation label").PointElevation = True

        vobj.addProperty(
            "App::PropertyBool", "Description", "Labels Visibility",
            "Show/hide description label").Description = False

        vobj.addProperty(
            "App::PropertyColor", "LabelColor", "Label Style",
            "Color of point labels").LabelColor = (1.0, 1.0, 1.0)

        vobj.addProperty(
            "App::PropertyFloat", "LabelSize", "Label Style",
            "Size of point labels").LabelSize = .2

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
            "App::PropertyFloat", "OffsetX", "Label Placement",
            "Horizontal offset between point labels and marker").OffsetX = .1

        vobj.addProperty(
            "App::PropertyFloat", "OffsetY", "Label Placement",
            "Vertical offset between point labels and marker").OffsetY = 0

        vobj.addProperty(
            "App::PropertyVector", "LabelOffset", "Label Placement",
            "Points of reference for point labels").LabelOffset = FreeCAD.Vector(vobj.OffsetX, vobj.OffsetY)

        vobj.addProperty(
            "App::PropertyPythonObject", "LabelDisplay", "Label Style", 
            "Keeper property for label visibilities").LabelDisplay = {
                "Number": vobj.Number,
                "Label": vobj.Label,
                "Easting": vobj.Easting,
                "Northing": vobj.Northing,
                "PointElevation": vobj.PointElevation,
                "Description": vobj.Description}

        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        self.Object = vobj.Object

        self.move = coin.SoTranslation()

        #-------------------------------------------------------------
        # Marker
        #-------------------------------------------------------------

        self.marker_color = coin.SoBaseColor()
        self.coordinate = coin.SoCoordinate3()
        self.line = coin.SoIndexedLineSet()
        geometry = coin.SoPointSet()

        self.marker = coin.SoSeparator()
        self.marker.addChild(self.move)
        self.marker.addChild(self.marker_color)
        self.marker.addChild(self.coordinate)
        self.marker.addChild(self.line)
        self.marker.addChild(geometry)

        #-------------------------------------------------------------
        # Frames
        #-------------------------------------------------------------

        self.circle_coordinate = coin.SoCoordinate3()
        self.circle_line = coin.SoLineSet()
        
        self.circle_frame = coin.SoSeparator()
        self.circle_frame.addChild(self.move)
        self.circle_frame.addChild(self.circle_coordinate)
        self.circle_frame.addChild(self.circle_line)

        self.square_coordinate = coin.SoCoordinate3()
        self.square_line = coin.SoLineSet()

        self.square_frame = coin.SoGeoSeparator()
        self.square_frame.addChild(self.move)
        self.square_frame.addChild(self.square_coordinate)
        self.square_frame.addChild(self.square_line)
        
        #-------------------------------------------------------------
        # Labels
        #-------------------------------------------------------------

        self.font = coin.SoFont()
        self.location = coin.SoTranslation()
        self.label_color = coin.SoBaseColor()
        self.text = coin.SoAsciiText()

        self.label = coin.SoSeparator()
        self.label.addChild(self.move)
        self.label.addChild(self.font)
        self.label.addChild(self.location)
        self.label.addChild(self.label_color)
        self.label.addChild(self.text)

        #-------------------------------------------------------------
        # Level of Detail
        #-------------------------------------------------------------

        level0 = coin.SoAnnotation()
        level0.addChild(self.label)
        level0.addChild(self.marker)
        level0.addChild(self.circle_frame)
        level0.addChild(self.square_frame)

        level1 = coin.SoAnnotation()
        level1.addChild(self.label)
        level1.addChild(self.marker)

        level2 = coin.SoAnnotation()
        level2.addChild(self.marker)

        lod = coin.SoLevelOfDetail()
        lod.addChild(level0)
        lod.addChild(level1)
        lod.addChild(level2)

        lod.screenArea.values = [500, 100]

        #-------------------------------------------------------------
        # Point
        #-------------------------------------------------------------

        self.drag_group = coin.SoSeparator()

        self.geosystem = coin.SoGeoSeparator()
        self.geosystem.addChild(self.drag_group)
        self.geosystem.addChild(lod)

        point = coin.SoType.fromName('SoFCSelection').createInstance()
        point.style = 'EMISSIVE_DIFFUSE'
        point.addChild(self.geosystem)

        vobj.addDisplayMode(point,"Point")

        #-------------------------------------------------------------
        # Initialize
        #-------------------------------------------------------------

        self.onChanged(vobj, "MarkerType")
        self.onChanged(vobj, "MarkerColor")
        self.onChanged(vobj, "MarkerSize")
        self.onChanged(vobj, "CircleFrame")
        #self.onChanged(vobj, "SquareFrame")
        self.onChanged(vobj, "LabelDisplay")
        self.onChanged(vobj, "LabelOffset")
        self.onChanged(vobj, "LabelColor")
        self.onChanged(vobj, "LabelSize")
        self.onChanged(vobj, "FontName")
        self.onChanged(vobj, "Justification")
        self.onChanged(vobj, "LineSpacing")

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        if prop == "Placement":
            placement = obj.getPropertyByName(prop)
            base = placement.Base

            origin = georigin(base)
            geo_system = ["UTM", origin.UtmZone, "FLAT"]
            self.geosystem.geoSystem.setValues(geo_system)
            self.geosystem.geoCoords.setValue(base.x, base.y, base.z)

            self.onChanged(obj.ViewObject, "LabelDisplay")

        if prop in ["Name", "Number"]:
            self.onChanged(obj.ViewObject, "LabelDisplay")

    def onChanged(self, vobj, prop):
        """Update Object visuals when a view property changed."""
        if prop == "MarkerType":
            type = vobj.getPropertyByName(prop)
            horizontal = FreeCAD.Vector(vobj.MarkerSize * 1000, 0, 0)
            vertical = FreeCAD.Vector(0, vobj.MarkerSize * 1000, 0)

            if type == "Point": 
                self.coordinate.point.values = [FreeCAD.Vector()]

            elif type == "Empty": 
                self.coordinate.point.values = []

            elif type == "Plus": 
                self.coordinate.point.values = [
                    vertical, 
                    vertical.negative(), 
                    horizontal, 
                    horizontal.negative()]

                self.line.coordIndex.values = [0, 1, -1, 2, 3, -1]

            elif type == "Cross": 
                self.coordinate.point.values = [
                    vertical.add(horizontal), 
                    vertical.negative().add(horizontal.negative()), 
                    vertical.negative().add(horizontal), 
                    vertical.add(horizontal.negative())]

                self.line.coordIndex.values = [0, 1, -1, 2, 3, -1]

            elif type == "Line": 
                self.coordinate.point.values = [
                    vertical.multiply(.5), 
                    FreeCAD.Vector()]

                self.line.coordIndex.values = [0, 1, -1]

        elif prop == "CircleFrame":
            if vobj.getPropertyByName(prop):
                radius = vobj.MarkerSize * 1000 / 2
                num_points = 16
                points = []
                for i in range(num_points):
                    angle = math.radians((360 / num_points) * i)
                    x = radius * math.cos(angle)
                    y = radius * math.sin(angle)
                    points.append(FreeCAD.Vector(x, y))
                points.append(points[0])

                self.circle_coordinate.point.values = points

        elif prop == "SquareFrame":
            horizontal = FreeCAD.Vector(vobj.MarkerSize * 1000 / 2, 0, 0)
            vertical = FreeCAD.Vector(0, vobj.MarkerSize * 1000 / 2, 0)
            if vobj.getPropertyByName(prop):
                self.square_coordinate.point.values = [
                    vertical.add(horizontal), 
                    vertical.add(horizontal.negative()), 
                    vertical.negative().add(horizontal.negative()), 
                    vertical.negative().add(horizontal), 
                    vertical.add(horizontal)]
            else:
                self.square_coordinate.point.values = []

        elif prop == "MarkerColor":
            color = vobj.getPropertyByName(prop)
            self.marker_color.rgb = color[:3]

        elif prop == "MarkerSize":
            self.onChanged(vobj, "MarkerType")

        elif prop == "Number":
            vobj.LabelDisplay[prop] = vobj.getPropertyByName(prop)
            self.onChanged(vobj, "LabelDisplay")

        elif prop == "Label":
            vobj.LabelDisplay[prop] = vobj.getPropertyByName(prop)
            self.onChanged(vobj, "LabelDisplay")

        elif prop == "Easting":
            vobj.LabelDisplay[prop] = vobj.getPropertyByName(prop)
            self.onChanged(vobj, "LabelDisplay")

        elif prop == "Northing":
            vobj.LabelDisplay[prop] = vobj.getPropertyByName(prop)
            self.onChanged(vobj, "LabelDisplay")

        elif prop == "PointElevation":
            vobj.LabelDisplay[prop] = vobj.getPropertyByName(prop)
            self.onChanged(vobj, "LabelDisplay")

        elif prop == "Description":
            vobj.LabelDisplay[prop] = vobj.getPropertyByName(prop)
            self.onChanged(vobj, "LabelDisplay")

        elif prop == "LabelColor":
            color = vobj.getPropertyByName(prop)
            self.label_color.rgb = color[:3]

        elif prop == "LabelSize":
            self.font.size = vobj.getPropertyByName(prop) * 1000
            self.onChanged(vobj, "OffsetY")

        elif prop == "FontName":
            self.font.name = vobj.getPropertyByName(prop).encode("utf8")

        elif prop == "Justification":
            justification = vobj.getPropertyByName(prop)
            if justification == "Left":
                self.text.justification = coin.SoAsciiText.LEFT
            elif justification == "Right":
                self.text.justification = coin.SoAsciiText.RIGHT
            else:
                self.text.justification = coin.SoAsciiText.CENTER
            self.onChanged(vobj, "OffsetX")

        elif prop == "LineSpacing":
            self.text.spacing = vobj.getPropertyByName(prop)

        elif prop == "OffsetX":
            justification = -1 if vobj.Justification == "Right" else 1
            vobj.LabelOffset.x = vobj.getPropertyByName(prop) * 1000 * justification
            self.onChanged(vobj, "LabelOffset")

        elif prop == "OffsetY":
            y_offset = vobj.getPropertyByName(prop)
            show = [key for key, value in vobj.LabelDisplay.items() if value]
            vobj.LabelOffset.y = vobj.LabelSize * 1000 * (len(show) / 2 - 1) + y_offset * 1000
            self.onChanged(vobj, "LabelOffset")

        elif prop == "LabelOffset":
            offset= vobj.getPropertyByName(prop)
            self.location.translation = offset

        elif prop == "LabelDisplay":
            display = vobj.getPropertyByName(prop)
            show = [key for key, value in display.items() if value]
            obj = vobj.Object

            label_set = [
                round(obj.getPropertyByName(prop), 3) 
                if isinstance(obj.getPropertyByName(prop), float)
                else obj.getPropertyByName(prop) for prop in show]

            self.text.string.setValues(label_set)
            self.onChanged(vobj, "OffsetY")

    def getDisplayModes(self, vobj):
        """Return a list of display modes."""
        modes=[]
        modes.append("Point")

        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode."""
        return "Point"

    def setDisplayMode(self,mode):
        """Map the display mode defined in attach with 
        those defined in getDisplayModes."""
        return mode

    def getIcon(self):
        """Return object treeview icon."""
        return icons_path + '/GeoPoint.svg'

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

    def dumps(self):
        """Called during document saving"""
        return None

    def loads(self, state):
        """Called during document restore."""
        return None
