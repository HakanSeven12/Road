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

"""Provides the viewprovider code for Region objects."""

import FreeCAD
from pivy import coin

import math

from ..variables import icons_path
from ..utils.get_group import georigin
from ..geoutils.alignment_old import transformation


class ViewProviderRegion:
    """This class is about Region Object view features."""
    def __init__(self, vobj):
        """Set view properties."""
        vobj.addProperty(
            "App::PropertyBool", "Labels", "Base",
            "Show/hide labels").Labels = True

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
            "Points of reference for station label").LabelOffset = FreeCAD.Vector(vobj.OffsetX, vobj.OffsetY)

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
        self.line_coords = coin.SoCoordinate3()
        self.line_lines = coin.SoIndexedLineSet()

        line_data = coin.SoGroup()
        line_data.addChild(self.line_coords)
        line_data.addChild(self.line_lines)

        # Line group
        lines = coin.SoAnnotation()
        lines.addChild(line_view)
        lines.addChild(line_data)


        #-----------------------------------------------------------------
        # Labels
        #-----------------------------------------------------------------

        # Text
        self.font = coin.SoFont()
        self.label_color = coin.SoBaseColor()

        self.texts = coin.SoGroup()

        self.labels = coin.SoSeparator()
        self.labels.addChild(self.font)
        self.labels.addChild(self.label_color)
        self.labels.addChild(self.texts)

        #-----------------------------------------------------------------
        # Region
        #-----------------------------------------------------------------

        # Standard group
        standard_selection = coin.SoType.fromName('SoFCSelection').createInstance()
        standard_selection.style = 'EMISSIVE_DIFFUSE'
        standard_selection.addChild(lines)
        standard_selection.addChild(self.labels)

        self.standard = coin.SoGeoSeparator()
        self.standard.addChild(standard_selection)

        vobj.addDisplayMode(self.standard, "Standard")

        self.onChanged(vobj, "Labels")
        self.onChanged(vobj, "LabelColor")
        self.onChanged(vobj, "LabelSize")
        self.onChanged(vobj, "FontName")
        self.onChanged(vobj, "Justification")


    def onChanged(self, vobj, prop):
        """Update Object visuals when a view property changed."""
        if prop == "Labels":
            self.texts.removeAllChildren()
            regions = vobj.Object.getParentGroup()
            alignment = regions.getParentGroup()

            tangent = vobj.Object.IncrementAlongTangents
            curve = vobj.Object.IncrementAlongCurves
            spiral = vobj.Object.IncrementAlongSpirals
            horizontal = vobj.Object.AtHorizontalAlignmentPoints

            stations = transformation(alignment, tangent, curve, spiral, horizontal)
            for station, transform in stations.items():
                point = transform["Location"]
                angle = transform["Rotation"]

                transform = coin.SoTransform()
                location = coin.SoTranslation()
                text = coin.SoAsciiText()


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

                station = str(station).zfill(6)
                integer = station.split('.')[0]
                new_integer = integer[:-3] + "+" + integer[-3:]

                text.string.setValues([new_integer + "." + station.split('.')[1]])

                group = coin.SoTransformSeparator()
                group.addChild(transform)
                group.addChild(location)
                group.addChild(text)
                self.texts.addChild(group)


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

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        if prop == "Placement":
            placement = obj.getPropertyByName(prop)
            origin = georigin(placement.Base)
            geo_system = ["UTM", origin.UtmZone, "FLAT"]

            self.standard.geoSystem.setValues(geo_system)
            self.standard.geoCoords.setValue(*placement.Base)

        elif prop == "Shape":
            shape = obj.getPropertyByName(prop).copy()
            shape.Placement.move(obj.Placement.Base.negative())

            line_coords, line_index = [], []
            for edge in shape.Edges:
                start = len(line_coords)
                line_coords.extend(edge.discretize(2))
                end = len(line_coords)

                line_index.extend(range(start,end))
                line_index.append(-1)

            self.line_coords.point.values = line_coords
            self.line_lines.coordIndex.values = line_index

    def getDisplayModes(self,vobj):
        """Return a list of display modes."""
        modes = ["Standard"]
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode."""
        return "Standard"

    def setDisplayMode(self,mode):
        """Map the display mode defined in attach with 
        those defined in getDisplayModes."""
        return mode

    def getIcon(self):
        """Return object treeview icon."""
        return icons_path + "/Region.svg"

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
