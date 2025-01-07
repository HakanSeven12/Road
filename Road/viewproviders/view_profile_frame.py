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

"""Provides the viewprovider code for Profile Frame objects."""

import FreeCAD, FreeCADGui
from pivy import coin

from ..variables import icons_path
from ..utils.get_group import georigin


class ViewProviderProfileFrame:
    """This class is about Profile Frame Object view features."""
    def __init__(self, vobj):
        """Set view properties."""

        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        self.Object = vobj.Object

        self.draw_style = coin.SoDrawStyle()
        self.draw_style.style = coin.SoDrawStyle.LINES

        #-----------------------------------------------------------------
        # Title
        #-----------------------------------------------------------------

        #-----------------------------------------------------------------
        # Border
        #-----------------------------------------------------------------

        # View
        self.border_color = coin.SoBaseColor()
        self.border_color.rgb = (0.0, 0.0, 1.0)

        border_view = coin.SoGroup()
        border_view.addChild(self.draw_style)
        border_view.addChild(self.border_color)

        # Data
        self.border_coords = coin.SoCoordinate3()
        self.border_lines = coin.SoLineSet()

        border_data = coin.SoGroup()
        border_data.addChild(self.border_coords)
        border_data.addChild(self.border_lines)

        # Group
        border = coin.SoSeparator()
        border.addChild(border_view)
        border.addChild(border_data)

        #-----------------------------------------------------------------
        # Grid
        #-----------------------------------------------------------------

        # View
        self.grid_color = coin.SoBaseColor()
        self.grid_color.rgb = (0.5, 0.5, 0.5)

        # Horizontal lines
        self.horizontal_coords = coin.SoCoordinate3()
        horizontal_lines = coin.SoLineSet()

        self.horizontal_copy = coin.SoMultipleCopy()
        self.horizontal_copy.addChild(self.horizontal_coords)
        self.horizontal_copy.addChild(horizontal_lines)

        horizontals = coin.SoSeparator()
        horizontals.addChild(self.grid_color)
        horizontals.addChild(self.horizontal_copy)

        # Vertical lines
        self.vertical_coords = coin.SoCoordinate3()
        vertical_lines = coin.SoLineSet()

        self.vertical_copy = coin.SoMultipleCopy()
        self.vertical_copy.addChild(self.vertical_coords)
        self.vertical_copy.addChild(vertical_lines)

        verticals = coin.SoSeparator()
        verticals.addChild(self.grid_color)
        verticals.addChild(self.vertical_copy)

        grid = coin.SoSeparator()
        grid.addChild(horizontals)
        grid.addChild(verticals)

        #-----------------------------------------------------------------
        # Labels
        #-----------------------------------------------------------------

        # View
        font = coin.SoFont()
        font.size = 1000

        # Horizon Label
        self.horizon = coin.SoAsciiText()
        self.horizon.justification = coin.SoAsciiText.RIGHT

        # Elevation Labels
        self.elevations = coin.SoSeparator()

        # Station Labels
        self.stations = coin.SoSeparator()

        # Label Group
        labels = coin.SoSeparator()
        labels.addChild(font)
        labels.addChild(self.horizon)
        labels.addChild(self.elevations)
        labels.addChild(self.stations)

        #-----------------------------------------------------------------
        # Profile Frame
        #-----------------------------------------------------------------

        # Frame group
        self.drag = coin.SoSeparator()
        self.frame = coin.SoGeoSeparator()
        self.frame.addChild(border)
        self.frame.addChild(grid)
        self.frame.addChild(labels)
        self.frame.addChild(self.drag)

        root = coin.SoType.fromName('SoFCSelection').createInstance()
        root.style = 'EMISSIVE_DIFFUSE'
        root.addChild(self.frame)

        vobj.addDisplayMode(root, "Frame")

    def onChanged(self, vobj, prop):
        """Update Object visuals when a view property changed."""
        pass

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        if prop == "Shape":
            shape = obj.getPropertyByName(prop)

            self.elevations.removeAllChildren()
            self.stations.removeAllChildren()
            if shape.Vertexes:
                origin = georigin()
                geo_system = ["UTM", origin.UtmZone, "FLAT"]
                reference = shape.Vertexes[0].Point

                self.frame.geoSystem.setValues(geo_system)
                self.frame.geoCoords.setValue(reference.x, reference.y, reference.z)
                corners = [ver.Point.add(reference.negative()) for ver in shape.Vertexes]
                corners.append(corners[0])
                self.border_coords.point.values = corners

                vertical_matrices = []
                for pos in range(10000, int(obj.Length), 10000):
                    matrix = coin.SbMatrix()
                    location = coin.SoTranslation()
                    station = coin.SoAsciiText()

                    matrix.setTransform(
                        coin.SbVec3f(pos, 0, -1), 
                        coin.SbRotation(), 
                        coin.SbVec3f(1.0, 1.0, 1.0))
                    vertical_matrices.append(matrix)

                    location.translation = coin.SbVec3f(pos, obj.Height+500, 0)
                    station.justification = coin.SoAsciiText.CENTER

                    text = str(round(pos / 1000, 2)).zfill(6)
                    integer = text.split('.')[0]
                    new_integer = integer[:-3] + "+" + integer[-3:]

                    station.string.setValues([new_integer + "." + text.split('.')[1]])

                    group = coin.SoTransformSeparator()
                    group.addChild(location)
                    group.addChild(station)
                    self.stations.addChild(group)

                self.vertical_coords.point.values = [corners[0], corners[3]]
                self.vertical_copy.matrix.values = vertical_matrices

                horizontal_matrices = []
                start = (obj.Horizon + 9999) // 10000 * 10000
                for pos in range(int(start), int(obj.Horizon+obj.Height), 10000):
                    matrix = coin.SbMatrix()
                    location = coin.SoTranslation()
                    elevation = coin.SoAsciiText()

                    matrix.setTransform(
                        coin.SbVec3f(0, pos-obj.Horizon, -1), 
                        coin.SbRotation(), 
                        coin.SbVec3f(1.0, 1.0, 1.0))
                    horizontal_matrices.append(matrix)

                    location.translation = coin.SbVec3f(-500, pos-obj.Horizon, 0)
                    elevation.justification = coin.SoAsciiText.RIGHT
                    elevation.string.setValues([round(pos/1000, 3)])

                    group = coin.SoTransformSeparator()
                    group.addChild(location)
                    group.addChild(elevation)
                    self.elevations.addChild(group)

                self.horizontal_coords.point.values = [corners[0], corners[1]]
                self.horizontal_copy.matrix.values = horizontal_matrices

        if prop == "Horizon":
            horizon = obj.getPropertyByName(prop)
            self.horizon.string.setValues(["Horizon Elevation", round(horizon/1000,3)])


    def getDisplayModes(self,vobj):
        """Return a list of display modes."""
        modes = ["Frame"]
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode."""
        return "Frame"

    def setDisplayMode(self,mode):
        """Map the display mode defined in attach with 
        those defined in getDisplayModes."""
        return mode

    def getIcon(self):
        """Return object treeview icon."""
        return icons_path + "/ProfileFrame.svg"

    def claimChildren(self):
        """Provides object grouping"""
        return self.Object.Group

    def dumps(self):
        """Called during document saving"""
        return None

    def loads(self, state):
        """Called during document restore."""
        return None
