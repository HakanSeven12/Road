# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Line objects."""

from pivy import coin
from .view_geo_object import ViewProviderGeoObject


class ViewProviderComponentLine(ViewProviderGeoObject):
    """This class is about Line Object view features."""
    def __init__(self, vobj):
        """Set view properties."""
        super().__init__(vobj, "ComponentLine")
        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        super().attach(vobj)

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

        self.standard.addChild(structure_selection)

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        super().updateData(obj, prop)

        if prop == "Shape":
            if  obj.Shape.Edges:
                self.line_coords.point.values = obj.Shape.discretize(2)

                component = obj.getParentGroup()
                if component:
                    side = coin.SoAsciiText.LEFT if component.Side == "Right" else coin.SoAsciiText.RIGHT
                    self.text.justification = side
                    self.location.translation = obj.Shape.CenterOfMass
                    self.text.string.setValues([obj.Label])