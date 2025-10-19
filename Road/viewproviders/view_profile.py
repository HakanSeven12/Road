# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Profile objects."""

import FreeCAD
from pivy import coin

from ..variables import icons_path
from ..utils.get_group import georigin


class ViewProviderProfile:
    """This class is about Profile Object view features."""
    def __init__(self, vobj):
        """Set view properties."""

        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        self.Object = vobj.Object

        self.draw_style = coin.SoDrawStyle()
        self.draw_style.style = coin.SoDrawStyle.LINES
        self.draw_style.lineWidth = 2

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
        # Circular
        #-----------------------------------------------------------------

        # Circular view
        self.circular_color = coin.SoBaseColor()
        
        circular_view = coin.SoGroup()
        circular_view.addChild(self.draw_style)
        circular_view.addChild(self.circular_color)

        # Circular data
        self.circular_coords = coin.SoCoordinate3()
        self.circular_lines = coin.SoIndexedLineSet()

        circular_data = coin.SoGroup()
        circular_data.addChild(self.circular_coords)
        circular_data.addChild(self.circular_lines)

        # Circular group
        circulars = coin.SoAnnotation()
        circulars.addChild(circular_view)
        circulars.addChild(circular_data)

        #-----------------------------------------------------------------
        # Parabola
        #-----------------------------------------------------------------

        # Parabola view
        self.parabola_color = coin.SoBaseColor()

        parabola_view = coin.SoGroup()
        parabola_view.addChild(self.draw_style)
        parabola_view.addChild(self.parabola_color)

        # Parabola data
        self.parabola_coords = coin.SoCoordinate3()
        self.parabola_lines = coin.SoIndexedLineSet()

        parabola_data = coin.SoGroup()
        parabola_data.addChild(self.parabola_coords)
        parabola_data.addChild(self.parabola_lines)

        # Parabola group
        parabolas = coin.SoAnnotation()
        parabolas.addChild(parabola_view)
        parabolas.addChild(parabola_data)

        #-----------------------------------------------------------------
        # Tangents
        #-----------------------------------------------------------------

        # Tangent view
        tangent_style = coin.SoDrawStyle()
        tangent_style.style = coin.SoDrawStyle.LINES
        tangent_style.lineWidth = 1
        tangent_style.linePattern = 0x739C
        tangent_style.linePatternScaleFactor = 3
        tangent_color = coin.SoBaseColor()
        tangent_color.rgb = (1.0, 1.0, 1.0)

        tangent_view = coin.SoGroup()
        tangent_view.addChild(tangent_style)
        tangent_view.addChild(tangent_color)

        # Tangent data
        self.tangent_coords = coin.SoCoordinate3()
        tangent_lines = coin.SoLineSet()

        tangent_data = coin.SoGroup()
        tangent_data.addChild(self.tangent_coords)
        tangent_data.addChild(tangent_lines)

        # Tangent group
        tangents = coin.SoSeparator()
        tangents.addChild(tangent_view)
        tangents.addChild(tangent_data)

        #-----------------------------------------------------------------
        # Profile
        #-----------------------------------------------------------------

        # Terrain group
        terrain_selection = coin.SoType.fromName('SoFCSelection').createInstance()
        terrain_selection.style = 'EMISSIVE_DIFFUSE'
        terrain_selection.addChild(lines)

        self.terrain = coin.SoGeoSeparator()
        self.terrain.addChild(terrain_selection)

        # Design group
        design_selection = coin.SoType.fromName('SoFCSelection').createInstance()
        design_selection.style = 'EMISSIVE_DIFFUSE'
        design_selection.addChild(lines)
        design_selection.addChild(circulars)
        design_selection.addChild(parabolas)
        design_selection.addChild(tangents)

        self.design = coin.SoGeoSeparator()
        self.design.addChild(design_selection)

        # Offset group
        offset_selection = coin.SoType.fromName('SoFCSelection').createInstance()
        offset_selection.style = 'EMISSIVE_DIFFUSE'
        offset_selection.addChild(lines)
        offset_selection.addChild(circulars)
        offset_selection.addChild(parabolas)

        self.offset = coin.SoGeoSeparator()
        self.offset.addChild(offset_selection)

        vobj.addDisplayMode(self.terrain, "Terrain")
        vobj.addDisplayMode(self.design, "Design")
        vobj.addDisplayMode(self.offset, "Offset")

    def onChanged(self, vobj, prop):
        """Update Object visuals when a view property changed."""
        if prop == "DisplayMode":
            mode = vobj.getPropertyByName(prop)
            if mode == "Terrain":
                self.line_color.rgb = (0.0, 1.0, 0.0)

                self.draw_style.lineWidth = 2

            elif mode == "Design":
                self.line_color.rgb = (1.0, 0.0, 0.0)
                self.parabola_color.rgb = (1.0, 1.0, 1.0)
                self.circular_color.rgb = (0.0, 0.0, 1.0)

                self.draw_style.lineWidth = 2

            elif mode == "Offset":
                color = (1.0, 1.0, 1.0)
                self.line_color.rgb = color
                self.parabola_color.rgb = color
                self.circular_color.rgb = color

                self.draw_style.lineWidth = 1


    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        if prop == "Placement":
            placement = obj.getPropertyByName(prop)
            origin = georigin()
            geo_system = ["UTM", origin.UtmZone, "FLAT"]

            self.terrain.geoSystem.setValues(geo_system)
            self.terrain.geoCoords.setValue(placement.Base.x, placement.Base.y, placement.Base.z)
            
            self.design.geoSystem.setValues(geo_system)
            self.design.geoCoords.setValue(placement.Base.x, placement.Base.y, placement.Base.z)

            self.offset.geoSystem.setValues(geo_system)
            self.offset.geoCoords.setValue(placement.Base.x, placement.Base.y, placement.Base.z)

        elif prop == "PVIs":
            pvi_list = obj.getPropertyByName(prop)
            self.tangent_coords.point.values = pvi_list

        elif prop == "Shape":
            shape = obj.getPropertyByName(prop).copy()
            shape.Placement.move(obj.Placement.Base.negative())

            line_coords = []
            circulars_coords = []
            parabolas_coords = []

            line_index = []
            circulars_index = []
            parabolas_index = []

            for wire in shape.Wires:
                for edge in wire.Edges:
                    if edge.Curve.TypeId == 'Part::GeomLine':
                        start = len(line_coords)
                        line_coords.extend(edge.discretize(2))
                        end = len(line_coords)

                        line_index.extend(range(start,end))
                        line_index.append(-1)

                    elif edge.Curve.TypeId == 'Part::GeomCircle':
                        start = len(circulars_coords)
                        circulars_coords.extend(edge.discretize(50))
                        end = len(circulars_coords)

                        circulars_index.extend(range(start,end))
                        circulars_index.append(-1)

                    elif edge.Curve.TypeId == 'Part::GeomBSplineCurve':
                        start = len(parabolas_coords)
                        parabolas_coords.extend(edge.discretize(50))
                        end = len(parabolas_coords)

                        parabolas_index.extend(range(start,end))
                        parabolas_index.append(-1)

            self.line_coords.point.values = line_coords
            self.line_lines.coordIndex.values = line_index
            self.circular_coords.point.values = circulars_coords
            self.circular_lines.coordIndex.values = circulars_index
            self.parabola_coords.point.values = parabolas_coords
            self.parabola_lines.coordIndex.values = parabolas_index

    def getDisplayModes(self,vobj):
        """Return a list of display modes."""
        modes = ["Terrain", "Design", "Offset"]
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode."""
        return "Design"

    def setDisplayMode(self,mode):
        """Map the display mode defined in attach with 
        those defined in getDisplayModes."""
        return mode

    def getIcon(self):
        """Return object treeview icon."""
        return icons_path + "/Profile.svg"

    def dumps(self):
        """Called during document saving"""
        return None

    def loads(self, state):
        """Called during document restore."""
        return None
