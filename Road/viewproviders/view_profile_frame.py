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

import FreeCAD
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
        self.border_coords = coin.SoGeoCoordinate()
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

        self.grid = coin.SoGeoSeparator()
        self.grid.addChild(horizontals)
        self.grid.addChild(verticals)

        #-----------------------------------------------------------------
        # Datum Label
        #-----------------------------------------------------------------

        #-----------------------------------------------------------------
        # Elevation Labels
        #-----------------------------------------------------------------

        #-----------------------------------------------------------------
        # Station Labels
        #-----------------------------------------------------------------

        #-----------------------------------------------------------------
        # Profile Frame
        #-----------------------------------------------------------------

        # Frame group
        frame = coin.SoType.fromName('SoFCSelection').createInstance()
        frame.style = 'EMISSIVE_DIFFUSE'
        frame.addChild(border)

        vobj.addDisplayMode(frame, "Frame")

    def onChanged(self, vobj, prop):
        """Update Object visuals when a view property changed."""
        pass

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        if prop == "Shape":
            shape = obj.getPropertyByName(prop)
            if shape.Vertexes:
                origin = georigin()
                geo_system = ["UTM", origin.UtmZone, "FLAT"]

                self.grid.geoSystem.setValues(geo_system)
                self.border_coords.geoSystem.setValues(geo_system)
                border_corners = [ver.Point for ver in shape.Vertexes]
                border_corners.append(border_corners[0])
                self.border_coords.point.values = border_corners

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
