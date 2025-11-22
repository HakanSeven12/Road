# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Geolocation based objects."""
from pivy import coin
from ..variables import icons_path
from ..utils.get_group import georigin


class ViewProviderGeoObject:
    """This class is about GeoObject view features."""
    def __init__(self, vobj, icon_name):
        self.icon = icons_path + f"/{icon_name}.svg"

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        self.flat_lines = coin.SoGeoSeparator()
        self.shaded = coin.SoGeoSeparator()
        self.wireframe = coin.SoGeoSeparator()
        self.points = coin.SoGeoSeparator()
        self.standard = coin.SoGeoSeparator()

        self.modes = {"Flat Lines": self.flat_lines,
                      "Shaded": self.shaded,
                      "Wireframe": self.wireframe,
                      "Points": self.points,
                      "Standard": self.standard}
        
        self.placement = coin.SoTranslation()

        for name, node in self.modes.items():
            node.addChild(self.placement)
            vobj.addDisplayMode(node, name)

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        if prop == "Geolocation":
            base = obj.Geolocation.Base
            origin = georigin(base)
            geo_system = ["UTM", origin.UtmZone, "FLAT"]
            self.flat_lines.geoSystem.setValues(geo_system)
            self.flat_lines.geoCoords.setValue(*base)

            self.shaded.geoSystem.setValues(geo_system)
            self.shaded.geoCoords.setValue(*base)

            self.wireframe.geoSystem.setValues(geo_system)
            self.wireframe.geoCoords.setValue(*base)

            self.points.geoSystem.setValues(geo_system)
            self.points.geoCoords.setValue(*base)
            
            self.standard.geoSystem.setValues(geo_system)
            self.standard.geoCoords.setValue(*base)

        if prop == "Placement":
            base = obj.Placement.Base
            self.placement.translation.setValue(*base.negative())
 
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
        return self.icon

    def dumps(self):
        """Called during document saving"""
        return self.icon

    def loads(self, state):
        """Called during document restore."""
        self.icon = state