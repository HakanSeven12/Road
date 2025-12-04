# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Line objects."""

import FreeCAD
from pivy import coin

from ..variables import icons_path
from ..utils.get_group import georigin


class ViewProviderComponentLine:
    """This class is about Line Object view features."""
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
        self.line_color.rgb = (1.0, 0.0, 1.0)

        line_view = coin.SoGroup()
        line_view.addChild(self.draw_style)
        line_view.addChild(self.line_color)

        # Line data
        self.line_coords = coin.SoCoordinate3()
        self.line_lines = coin.SoLineSet()

        line_data = coin.SoGroup()
        line_data.addChild(self.line_coords)
        line_data.addChild(self.line_lines)

        # Line group
        lines = coin.SoAnnotation()
        lines.addChild(line_view)
        lines.addChild(line_data)

        #-------------------------------------------------------------
        # Labels
        #-------------------------------------------------------------

        self.font = coin.SoFont()
        self.font.size = 250
        self.location = coin.SoTranslation()
        self.label_color = coin.SoBaseColor()
        self.label_color.rgb = (1.0, 0.0, 0.0)
        self.text = coin.SoAsciiText()

        self.label = coin.SoAnnotation()
        self.label.addChild(self.font)
        self.label.addChild(self.location)
        self.label.addChild(self.label_color)
        self.label.addChild(self.text)

        #-----------------------------------------------------------------
        # Line
        #-----------------------------------------------------------------

        # Terrain group
        structure_selection = coin.SoType.fromName('SoFCSelection').createInstance()
        structure_selection.style = 'EMISSIVE_DIFFUSE'
        structure_selection.addChild(lines)
        structure_selection.addChild(self.label)

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
            if not shape.Edges: return
            shape.Placement.move(obj.Placement.Base.negative())

            self.line_coords.point.values = shape.discretize(2)

            component = obj.getParentGroup()
            if component:
                side = coin.SoAsciiText.LEFT if component.Side == "Right" else coin.SoAsciiText.RIGHT
                self.text.justification = side
                self.location.translation = shape.CenterOfMass
                self.text.string.setValues([obj.Label])


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
        return icons_path + "/ComponentLine.svg"

    def dumps(self):
        """Called during document saving"""
        return None

    def loads(self, state):
        """Called during document restore."""
        return None
