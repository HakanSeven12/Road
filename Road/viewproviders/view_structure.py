# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Profile objects."""

from pivy import coin
from .view_geo_object import ViewProviderGeoObject


class ViewProviderStructure(ViewProviderGeoObject):
    """This class is about Profile Object view features."""
    def __init__(self, vobj):
        """Set view properties."""
        super().__init__(vobj, "Structure")
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

        self.standard.addChild(structure_selection)

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        super().updateData(obj, prop)

        if prop == "Shape":
            line_coords = []
            line_index = []
            for edge in obj.Shape.Edges:
                start = len(line_coords)
                line_coords.extend(edge.discretize(2))
                end = len(line_coords)

                line_index.extend(range(start,end))
                line_index.append(-1)

            self.line_coords.point.values = line_coords
            self.line_lines.coordIndex.values = line_index

    def claimChildren(self):
        """Provides object grouping"""
        return self.Object.Group
