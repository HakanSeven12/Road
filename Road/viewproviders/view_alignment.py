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

"""Provides the viewprovider code for Alignment objects."""

import FreeCAD
from pivy import coin

import math

from variables import icons_path
from ..utils.get_group import georigin
from ..functions.alignment import transformation


class ViewProviderAlignment:
    """This class is about Alignment Object view features."""
    def __init__(self, vobj):
        """Set view properties."""
        vobj.addProperty(
            "App::PropertyBool", "Labels", "Base",
            "Show/hide labels").Labels = False

        vobj.addProperty(
            "App::PropertyFloat", "TickSize", "Label Style",
            "Size of station tick").TickSize = 1

        vobj.addProperty(
            "App::PropertyColor", "LabelColor", "Label Style",
            "Color of station label").LabelColor = (1.0, 1.0, 1.0)

        vobj.addProperty(
            "App::PropertyFloat", "LabelSize", "Label Style",
            "Size of station label").LabelSize = 1

        vobj.addProperty(
            "App::PropertyFont", "FontName", "Label Style",
            "Font name of station label").FontName

        vobj.addProperty(
            "App::PropertyEnumeration", "Justification", "Label Placement",
            "Justification of station label").Justification = ["Left", "Center", "Right"]

        vobj.addProperty(
            "App::PropertyFloat", "OffsetX", "Label Placement",
            "Horizontal offset between station label and tick").OffsetX = 1

        vobj.addProperty(
            "App::PropertyFloat", "OffsetY", "Label Placement",
            "Vertical offset between point station and tick").OffsetY = 0

        vobj.addProperty(
            "App::PropertyVector", "LabelOffset", "Label Placement",
            "Points of referance for station label").LabelOffset = FreeCAD.Vector(vobj.OffsetX, vobj.OffsetY)

        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        self.Object = vobj.Object

        self.draw_style = coin.SoDrawStyle()
        self.draw_style.style = coin.SoDrawStyle.LINES

        #-----------------------------------------------------------------
        # Lines
        #-----------------------------------------------------------------

        # Line view
        self.line_color = coin.SoBaseColor()

        line_view = coin.SoGroup()
        line_view.addChild(self.draw_style)
        line_view.addChild(self.line_color)

        # Line data
        self.line_coords = coin.SoGeoCoordinate()
        self.line_lines = coin.SoIndexedLineSet()

        line_data = coin.SoGroup()
        line_data.addChild(self.line_coords)
        line_data.addChild(self.line_lines)

        # Line group
        lines = coin.SoSeparator()
        lines.addChild(line_view)
        lines.addChild(line_data)

        #-----------------------------------------------------------------
        # Curves
        #-----------------------------------------------------------------

        # Curve view
        self.curve_color = coin.SoBaseColor()
        
        curve_view = coin.SoGroup()
        curve_view.addChild(self.draw_style)
        curve_view.addChild(self.curve_color)

        # Curve data
        self.curve_coords = coin.SoGeoCoordinate()
        self.curve_lines = coin.SoIndexedLineSet()

        curve_data = coin.SoGroup()
        curve_data.addChild(self.curve_coords)
        curve_data.addChild(self.curve_lines)

        # Curve group
        curves = coin.SoSeparator()
        curves.addChild(curve_view)
        curves.addChild(curve_data)

        #-----------------------------------------------------------------
        # Spirals
        #-----------------------------------------------------------------

        # Spiral view
        self.spiral_color = coin.SoBaseColor()

        spiral_view = coin.SoGroup()
        spiral_view.addChild(self.draw_style)
        spiral_view.addChild(self.spiral_color)

        # Spiral data
        self.spiral_coords = coin.SoGeoCoordinate()
        self.spiral_lines = coin.SoIndexedLineSet()

        spiral_data = coin.SoGroup()
        spiral_data.addChild(self.spiral_coords)
        spiral_data.addChild(self.spiral_lines)

        # Spiral group
        spirals = coin.SoSeparator()
        spirals.addChild(spiral_view)
        spirals.addChild(spiral_data)

        #-----------------------------------------------------------------
        # Tangents
        #-----------------------------------------------------------------

        # Tangent view
        tangent_style = coin.SoDrawStyle()
        tangent_style.style = coin.SoDrawStyle.LINES
        tangent_style.lineWidth = 1
        tangent_style.linePattern = 0x739C
        tangent_style.linePatternScaleFactor = 3
        tangent_color = coin.SoBaseColor()
        tangent_color.rgb = (1.0, 1.0, 1.0)

        tangent_view = coin.SoGroup()
        tangent_view.addChild(tangent_style)
        tangent_view.addChild(tangent_color)

        # Tangent data
        self.tangent_coords = coin.SoGeoCoordinate()
        tangent_lines = coin.SoLineSet()

        tangent_data = coin.SoGroup()
        tangent_data.addChild(self.tangent_coords)
        tangent_data.addChild(tangent_lines)

        # Tangent group
        tangents = coin.SoSeparator()
        tangents.addChild(tangent_view)
        tangents.addChild(tangent_data)

        #-----------------------------------------------------------------
        # Labels
        #-----------------------------------------------------------------

        #Ticks
        self.tick_coords = coin.SoCoordinate3()
        tick_lines = coin.SoLineSet()

        self.tick_copy = coin.SoMultipleCopy()
        self.tick_copy.addChild(self.tick_coords)
        self.tick_copy.addChild(tick_lines)

        # Text
        self.font = coin.SoFont()
        self.font.size = 3000
        self.label_color = coin.SoBaseColor()

        self.texts = coin.SoGroup()

        self.labels = coin.SoGeoSeparator()
        self.labels.addChild(self.font)
        self.labels.addChild(self.label_color)
        self.labels.addChild(self.tick_copy)
        self.labels.addChild(self.texts)

        #-----------------------------------------------------------------
        # Alignment
        #-----------------------------------------------------------------

        # Centerline group
        centerline = coin.SoType.fromName('SoFCSelection').createInstance()
        centerline.style = 'EMISSIVE_DIFFUSE'
        centerline.addChild(lines)
        centerline.addChild(curves)
        centerline.addChild(spirals)
        centerline.addChild(tangents)
        centerline.addChild(self.labels)

        # Offset group
        offset = coin.SoType.fromName('SoFCSelection').createInstance()
        offset.style = 'EMISSIVE_DIFFUSE'
        offset.addChild(lines)
        offset.addChild(curves)
        offset.addChild(spirals)

        vobj.addDisplayMode(centerline, "Centerline")
        vobj.addDisplayMode(offset, "Offset")

        self.onChanged(vobj, "Labels")
        #self.onChanged(vobj, "TickSize")
        self.onChanged(vobj, "LabelColor")
        self.onChanged(vobj, "LabelSize")
        self.onChanged(vobj, "FontName")
        self.onChanged(vobj, "Justification")


    def onChanged(self, vobj, prop):
        """Update Object visuals when a view property changed."""
        if prop == "Labels":
            self.texts.removeAllChildren()
            if not vobj.getPropertyByName(prop):
                self.tick_coords.point.values = []
                return

            start = vobj.Object.StartStation.Value
            end = vobj.Object.EndStation.Value
            increment = 10000
            stations = list(range(int(start), int(end), increment))
            points, rotations = transformation(vobj.Object.Shape, stations, True)
            stations.append(end)
            if not points: return

            matrices = []
            for i, station in enumerate(stations):
                matrix = coin.SbMatrix()
                transform = coin.SoTransform()
                location = coin.SoTranslation()
                text = coin.SoAsciiText()

                point = points[i].sub(georigin().Base)
                angle = rotations[i]

                matrix.setTransform(
                    coin.SbVec3f(point.x, point.y, point.z), 
                    coin.SbRotation(coin.SbVec3f(0, 0, 1), angle), 
                    coin.SbVec3f(1.0, 1.0, 1.0))
                matrices.append(matrix)

                if vobj.Justification == "Left":
                    text.justification = coin.SoAsciiText.LEFT
                elif vobj.Justification == "Right":
                    text.justification = coin.SoAsciiText.RIGHT
                else:
                    text.justification = coin.SoAsciiText.CENTER

                if math.pi / 2 < angle < 3 * math.pi /2:
                    text.justification = 2 if text.justification == 1 else 1
                    angle = (angle + math.pi) % (2 * math.pi)

                transform.translation = point
                transform.rotation.setValue(coin.SbVec3f(0, 0, 1), angle)
                location.translation = vobj.LabelOffset

                station = str(round(station / 1000, 2)).zfill(6)
                integer = station.split('.')[0]
                new_integer = integer[:-3] + "+" + integer[-3:]

                text.string.setValues([new_integer + "." + station.split('.')[1]])

                group = coin.SoTransformSeparator()
                group.addChild(transform)
                group.addChild(location)
                group.addChild(text)
                self.texts.addChild(group)

            self.tick_copy.matrix.values = matrices

        elif prop == "TickSize":
            size = vobj.getPropertyByName(prop)
            self.tick_coords.point.values = [
                FreeCAD.Vector((size / 2) * 1000, 0, 0), 
                FreeCAD.Vector((-size / 2) * 1000, 0, 0)]

        elif prop == "LabelColor":
            color = vobj.getPropertyByName(prop)
            self.label_color.rgb = (color[0], color[1], color[2])

        elif prop == "LabelSize":
            self.font.size = vobj.getPropertyByName(prop) * 1000
            self.onChanged(vobj, "OffsetY")

        elif prop == "FontName":
            self.font.name = vobj.getPropertyByName(prop).encode("utf8")

        elif prop == "Justification":
            self.onChanged(vobj, "OffsetX")

        elif prop == "OffsetX":
            justification = -1 if vobj.Justification == "Right" else 1
            vobj.LabelOffset.x = vobj.getPropertyByName(prop) * 1000 * justification
            self.onChanged(vobj, "LabelOffset")

        elif prop == "OffsetY":
            y_offset = vobj.getPropertyByName(prop)
            vobj.LabelOffset.y = -vobj.LabelSize / 2 + y_offset * 1000
            self.onChanged(vobj, "LabelOffset")

        elif prop == "LabelOffset":
            self.onChanged(vobj, "Labels")

        if prop == "DisplayMode":
            mode = vobj.getPropertyByName(prop)
            if mode == "Centerline":
                self.line_color.rgb = (1.0, 0.0, 0.0)
                self.spiral_color.rgb = (0.0, 0.0, 1.0)
                self.curve_color.rgb = (0.0, 1.0, 0.0)

                self.draw_style.lineWidth = 2

            if mode == "Offset":
                color = (1.0, 1.0, 1.0)
                self.line_color.rgb = color
                self.spiral_color.rgb = color
                self.curve_color.rgb = color

                self.draw_style.lineWidth = 1

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        if prop == "PIs":
            pi_list = obj.getPropertyByName(prop)
            if pi_list:
                # Coordinate system
                origin = georigin(pi_list[0])
                geo_system = ["UTM", origin.UtmZone, "FLAT"]

                self.line_coords.geoSystem.setValues(geo_system)
                self.curve_coords.geoSystem.setValues(geo_system)
                self.spiral_coords.geoSystem.setValues(geo_system)
                self.tangent_coords.geoSystem.setValues(geo_system)
                self.tangent_coords.point.values = pi_list
                self.labels.geoSystem.setValues(geo_system)
                self.labels.geoCoords.setValue(origin.Base.x, origin.Base.y, origin.Base.z)

        if prop == "Shape":
            shape = obj.getPropertyByName(prop)
            if shape.SubShapes:
                line_coords = []
                curves_coords = []
                spirals_coords = []

                line_index = []
                curves_index = []
                spirals_index = []

                for shp in shape.SubShapes:
                    if shp.Curve.TypeId == 'Part::GeomLine':
                        start = len(line_coords)
                        line_coords.extend(shp.discretize(2))
                        end = len(line_coords)

                        line_index.extend(range(start,end))
                        line_index.append(-1)

                    elif shp.Curve.TypeId == 'Part::GeomCircle':
                        start = len(curves_coords)
                        curves_coords.extend(shp.discretize(50))
                        end = len(curves_coords)

                        curves_index.extend(range(start,end))
                        curves_index.append(-1)

                    elif shp.Curve.TypeId == 'Part::GeomBSplineCurve':
                        start = len(spirals_coords)
                        spirals_coords.extend(shp.discretize(50))
                        end = len(spirals_coords)

                        spirals_index.extend(range(start,end))
                        spirals_index.append(-1)

                self.line_coords.point.values = line_coords
                self.line_lines.coordIndex.values = line_index
                self.curve_coords.point.values = curves_coords
                self.curve_lines.coordIndex.values = curves_index
                self.spiral_coords.point.values = spirals_coords
                self.spiral_lines.coordIndex.values = spirals_index

    def getDisplayModes(self,vobj):
        """Return a list of display modes."""
        modes = ["Centerline", "Offset", "Curb Return", "Rail", "Miscellaneous"]
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode."""
        return "Centerline"

    def setDisplayMode(self,mode):
        """Map the display mode defined in attach with 
        those defined in getDisplayModes."""
        return mode

    def getIcon(self):
        """Return object treeview icon."""
        return icons_path + "/Alignment.svg"

    def claimChildren(self):
        """Provides object grouping"""
        return self.Object.Group

    def setEdit(self, vobj, mode=0):
        """Enable edit"""
        return True

    def unsetEdit(self, vobj, mode=0):
        """Disable edit"""
        return False

    def doubleClicked(self, vobj):
        """Detect double click"""
        pass

    def setupContextMenu(self, obj, menu):
        """Context menu construction"""
        pass

    def edit(self):
        """Edit callback"""
        pass

    def dumps(self):
        """Called during document saving"""
        return None

    def loads(self, state):
        """Called during document restore."""
        return None
