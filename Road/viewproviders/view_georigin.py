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

"""Provides the viewprovider code for Geo Origin objects."""
import FreeCADGui
from pivy import coin
from .view_group import ViewProviderGroup


class ViewProviderGeoOrigin(ViewProviderGroup):
    """This class is about Point Group Object view features."""

    def __init__(self, vobj, icon):
        """Set view properties."""
        super().__init__(vobj, icon)

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        if prop == "UtmZone":
            origin = self.get_geoorigin()
            zone = obj.getPropertyByName(prop)
            geo_system = ["UTM", zone, "FLAT"]
            origin.geoSystem.setValues(geo_system)

        if prop == "Base":
            origin = self.get_geoorigin()
            base = obj.getPropertyByName(prop)
            origin.geoCoords.setValue(base.x, base.y, 0)

    def getDisplayModes(self, vobj):
        """Return a list of display modes."""
        modes=["GoeOrigin"]
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode."""
        return "GoeOrigin"

    def setDisplayMode(self,mode):
        """Map the display mode defined in attach with 
        those defined in getDisplayModes."""
        return mode

    def get_geoorigin(self):
        scene_graph = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
        node = scene_graph.getChild(0)

        if isinstance(node, coin.SoGeoOrigin):
            return node

        origin = coin.SoGeoOrigin()
        scene_graph.insertChild(origin,0)
        return origin
