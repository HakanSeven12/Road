# SPDX-License-Identifier: LGPL-2.1-or-later

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
        modes=["GeoOrigin"]
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode."""
        return "GeoOrigin"

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
