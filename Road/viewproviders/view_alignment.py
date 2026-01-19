# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Alignment objects."""

import FreeCAD
from pivy import coin
from .view_geo_object import ViewProviderGeoObject
from ..utils.label_manager import LabelManager
from ..utils.support import  zero_referance

import math


class ViewProviderAlignment(ViewProviderGeoObject):
    """This class is about Alignment Object view features."""
    def __init__(self, vobj):
        """Set view properties."""
        super().__init__(vobj, "Alignment")

        vobj.addProperty(
            "App::PropertyBool", "Labels", "Base",
            "Show/hide labels").Labels = False

        vobj.addProperty(
            "App::PropertyFloat", "TickSize", "Label Style",
            "Size of station tick").TickSize = 1

        vobj.addProperty(
            "App::PropertyColor", "LabelColor", "Label Style",
            "Color of station label").LabelColor = (1.0, 1.0, 1.0)

        vobj.addProperty(
            "App::PropertyFloat", "LabelSize", "Label Style",
            "Size of station label").LabelSize = 1

        vobj.addProperty(
            "App::PropertyFont", "FontName", "Label Style",
            "Font name of station label").FontName

        vobj.addProperty(
            "App::PropertyEnumeration", "Justification", "Label Placement",
            "Justification of station label").Justification = ["Left", "Center", "Right"]

        vobj.addProperty(
            "App::PropertyPlacement", "Transformation", "Label Placement",
            "Placement").Transformation = FreeCAD.Placement()

        vobj.Proxy = self
        self.label_manager = None

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        super().attach(vobj)

        self.Object = vobj.Object

        self.draw_style = coin.SoDrawStyle()
        self.draw_style.style = coin.SoDrawStyle.LINES

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
        # Curves
        #-----------------------------------------------------------------

        # Curve view
        self.curve_color = coin.SoBaseColor()
        
        curve_view = coin.SoGroup()
        curve_view.addChild(self.draw_style)
        curve_view.addChild(self.curve_color)

        # Curve data
        self.curve_coords = coin.SoCoordinate3()
        self.curve_lines = coin.SoIndexedLineSet()

        curve_data = coin.SoGroup()
        curve_data.addChild(self.curve_coords)
        curve_data.addChild(self.curve_lines)

        # Curve group
        curves = coin.SoAnnotation()
        curves.addChild(curve_view)
        curves.addChild(curve_data)

        #-----------------------------------------------------------------
        # Spirals
        #-----------------------------------------------------------------

        # Spiral view
        self.spiral_color = coin.SoBaseColor()

        spiral_view = coin.SoGroup()
        spiral_view.addChild(self.draw_style)
        spiral_view.addChild(self.spiral_color)

        # Spiral data
        self.spiral_coords = coin.SoCoordinate3()
        self.spiral_lines = coin.SoIndexedLineSet()

        spiral_data = coin.SoGroup()
        spiral_data.addChild(self.spiral_coords)
        spiral_data.addChild(self.spiral_lines)

        # Spiral group
        spirals = coin.SoAnnotation()
        spirals.addChild(spiral_view)
        spirals.addChild(spiral_data)

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
        # Labels
        #-----------------------------------------------------------------

        labels_root = coin.SoSeparator()
        self.label_manager = LabelManager(labels_root)

        #-----------------------------------------------------------------
        # Alignment
        #-----------------------------------------------------------------

        # Centerline group
        centerline_selection = coin.SoType.fromName('SoFCSelection').createInstance()
        centerline_selection.style = 'EMISSIVE_DIFFUSE'
        centerline_selection.addChild(lines)
        centerline_selection.addChild(curves)
        centerline_selection.addChild(spirals)
        centerline_selection.addChild(tangents)
        centerline_selection.addChild(labels_root)

        self.standard.addChild(centerline_selection)

        # Offset group
        offset_selection = coin.SoType.fromName('SoFCSelection').createInstance()
        offset_selection.style = 'EMISSIVE_DIFFUSE'
        offset_selection.addChild(lines)
        offset_selection.addChild(curves)
        offset_selection.addChild(spirals)

        self.offset = coin.SoGeoSeparator()
        self.offset.addChild(centerline_selection)

        vobj.addDisplayMode(self.offset, "Offset")

        self.onChanged(vobj, "Labels")
        self.onChanged(vobj, "LabelColor")
        self.onChanged(vobj, "LabelSize")
        self.onChanged(vobj, "FontName")
        self.onChanged(vobj, "Justification")


    def onChanged(self, vobj, prop):
        """Update Object visuals when a view property changed."""
        if prop == "Labels":
            if not hasattr(vobj, 'Transformation') or not hasattr(vobj, 'Model'):
                return
                
            self.label_manager.clear_labels()
            stations = vobj.Object.Model.generate_stations()
            
            for station in stations:
                # Get point and direction from alignment
                tuple_coord, tuple_vec = vobj.Object.Model.get_orthogonal_at_station(station, "left")
                coord = zero_referance(vobj.Object.Model.get_start_point(), [tuple_coord])
                point = coord[0].add(vobj.Object.Placement.Base)
                dir_vec = FreeCAD.Vector(*tuple_vec)
                
                # Calculate angle from direction vector
                angle = math.atan2(dir_vec.y, dir_vec.x)

                # Prepare placement and rotation
                placement = FreeCAD.Placement()
                placement.Base = FreeCAD.Vector(0, 0, 0)
                placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), math.degrees(angle))
                
                # Adjust for readability
                justification = vobj.Justification
                if math.pi / 2 < angle < 3 * math.pi / 2:
                    if justification == "Left":
                        justification = "Right"
                    elif justification == "Right":
                        justification = "Left"
                    angle = (angle + math.pi) % (2 * math.pi)
                    placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), math.degrees(angle))

                # Format station text
                km = int(station // 1000)
                m = station - km * 1000
                text = f"{km}+{m:06.2f}"

                self.label_manager.add_label(
                    position=point,
                    text=text,
                    side=justification,
                    spacing=1.0,
                    transformation=placement.multiply(vobj.Transformation)
                )

        elif prop == "LabelColor":
            if self.label_manager:
                color = vobj.getPropertyByName(prop)
                self.label_manager.material.diffuseColor = (color[0], color[1], color[2])

        elif prop == "LabelSize":
            if self.label_manager:
                self.label_manager.font.size = vobj.getPropertyByName(prop) * 1000
            self.onChanged(vobj, "Labels")

        elif prop == "FontName":
            if self.label_manager:
                self.label_manager.font.name = vobj.getPropertyByName(prop).encode("utf8")

        elif prop == "Justification":
            self.onChanged(vobj, "Labels")

        elif prop == "Transformation":
            self.onChanged(vobj, "Labels")

        elif prop == "DisplayMode":
            mode = vobj.getPropertyByName(prop)
            if mode == "Standard":
                self.line_color.rgb = (1.0, 0.0, 0.0)
                self.spiral_color.rgb = (0.0, 1.0, 0.0)
                self.curve_color.rgb = (0.0, 0.0, 1.0)

                self.draw_style.lineWidth = 2

            elif mode == "Offset":
                color = (1.0, 1.0, 1.0)
                self.line_color.rgb = color
                self.spiral_color.rgb = color
                self.curve_color.rgb = color

                self.draw_style.lineWidth = 1

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        super().updateData(obj, prop)
        if prop == "PIs":
            self.tangent_coords.point.values = obj.PIs

        elif prop == "Shape":
            line_coords, line_index = [], []
            curves_coords, curves_index = [], []
            spirals_coords, spirals_index = [], []
            for edge in obj.Shape.Edges:
                if edge.Curve.TypeId == 'Part::GeomLine':
                    start = len(line_coords)
                    line_coords.extend(edge.discretize(2))
                    end = len(line_coords)

                    line_index.extend(range(start,end))
                    line_index.append(-1)

                elif edge.Curve.TypeId == 'Part::GeomCircle':
                    start = len(curves_coords)
                    curves_coords.extend(edge.discretize(50))
                    end = len(curves_coords)

                    curves_index.extend(range(start,end))
                    curves_index.append(-1)

                elif edge.Curve.TypeId == 'Part::GeomBSplineCurve':
                    start = len(spirals_coords)
                    spirals_coords.extend(edge.discretize(50))
                    end = len(spirals_coords)

                    spirals_index.extend(range(start,end))
                    spirals_index.append(-1)

            self.line_coords.point.values = line_coords
            self.line_lines.coordIndex.values = line_index
            self.curve_coords.point.values = curves_coords
            self.curve_lines.coordIndex.values = curves_index
            self.spiral_coords.point.values = spirals_coords
            self.spiral_lines.coordIndex.values = spirals_index

    def claimChildren(self):
        """Provides object grouping"""
        return self.Object.Group