# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Profile objects."""

import FreeCAD
from pivy import coin

from ..variables import icons_path
from ..utils.get_group import georigin


class ViewProviderStructure:
    """This class is about Profile Object view features."""
    def __init__(self, vobj):
        """Set view properties."""

        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        self.Object = vobj.Object

        self.draw_style = coin.SoDrawStyle()
        self.draw_style.style = coin.SoDrawStyle.LINES
        self.draw_style.lineWidth = 1

        #-----------------------------------------------------------------
        # Lines
        #-----------------------------------------------------------------

        # Line view
        self.line_color = coin.SoBaseColor()
        self.line_color.rgb = (1.0, 0.0, 0.0)

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
        # Profile
        #-----------------------------------------------------------------

        # Terrain group
        structure_selection = coin.SoType.fromName('SoFCSelection').createInstance()
        structure_selection.style = 'EMISSIVE_DIFFUSE'
        structure_selection.addChild(lines)

        self.structure = coin.SoGeoSeparator()
        self.structure.addChild(structure_selection)

        vobj.addDisplayMode(self.structure, "Flat Lines")

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        if prop == "Placement":
            placement = obj.getPropertyByName(prop)
            origin = georigin()
            geo_system = ["UTM", origin.UtmZone, "FLAT"]

            self.structure.geoSystem.setValues(geo_system)
            self.structure.geoCoords.setValue(placement.Base.x, placement.Base.y, placement.Base.z)

        elif prop == "Shape":
            shape = obj.getPropertyByName(prop).copy()
            shape.Placement.move(obj.Placement.Base.negative())

            line_coords = []
            line_index = []
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
        modes = ["Flat Lines"]
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode."""
        return "Flat Lines"

    def setDisplayMode(self,mode):
        """Map the display mode defined in attach with 
        those defined in getDisplayModes."""
        return mode

    def getIcon(self):
        """Return object treeview icon."""
        return icons_path + "/Structure.svg"

    def claimChildren(self):
        """Provides object grouping"""
        return self.Object.Group

    def dumps(self):
        """Called during document saving"""
        return None

    def loads(self, state):
        """Called during document restore."""
        return None
