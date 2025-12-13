# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Region objects."""

import FreeCAD
from pivy import coin
import math
from .view_geo_object import ViewProviderGeoObject
from ..utils.label_manager import LabelManager
from ..utils.support import  zero_referance


class ViewProviderRegion(ViewProviderGeoObject):
    """This class is about Region Object view features."""
    def __init__(self, vobj):
        """Set view properties."""
        super().__init__(vobj, "Region")
        vobj.addProperty(
            "App::PropertyBool", "Labels", "Base",
            "Show/hide labels").Labels = True

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
        # Labels
        #-----------------------------------------------------------------

        labels_root = coin.SoSeparator()
        self.label_manager = LabelManager(labels_root)

        #-----------------------------------------------------------------
        # Region
        #-----------------------------------------------------------------

        # Standard group
        standard_selection = coin.SoType.fromName('SoFCSelection').createInstance()
        standard_selection.style = 'EMISSIVE_DIFFUSE'
        standard_selection.addChild(lines)
        standard_selection.addChild(labels_root)

        self.standard.addChild(standard_selection)

        vobj.addDisplayMode(self.standard, "Standard")

        self.onChanged(vobj, "Labels")
        self.onChanged(vobj, "LabelColor")
        self.onChanged(vobj, "LabelSize")
        self.onChanged(vobj, "FontName")
        self.onChanged(vobj, "Justification")


    def onChanged(self, vobj, prop):
        """Update Object visuals when a view property changed."""
        if prop == "Labels":
            if not hasattr(self, 'label_manager') or self.label_manager is None:
                return
            if not hasattr(vobj, 'Transformation'):
                return
                
            self.label_manager.clear_labels()
            
            if not vobj.Labels:
                return
                
            regions = vobj.Object.getParentGroup()
            alignment = regions.getParentGroup()

            for station in vobj.Object.Stations:
                # Get point and direction from alignment
                tuple_coord, tuple_vec = alignment.Model.get_orthogonal_at_station(station, "left")
                coord = zero_referance(alignment.Model.get_start_point(), [tuple_coord])
                point = coord[0].add(alignment.Placement.Base)
                dir_vec = FreeCAD.Vector(*tuple_vec)
                
                # Calculate angle from direction vector
                angle = math.atan2(dir_vec.y, dir_vec.x)
                
                # Prepare placement and rotation
                placement = FreeCAD.Placement()
                placement.Base = FreeCAD.Vector(0, 0, 0)
                placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), math.degrees(angle))

                # Format station text
                station_str = str(station).zfill(6)
                integer = station_str.split('.')[0]
                new_integer = integer[:-3] + "+" + integer[-3:]
                text = new_integer + "." + station_str.split('.')[1]
                
                self.label_manager.add_label(
                    position=point,
                    text=text,
                    side=vobj.Justification,
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

        elif prop == "OffsetX":
            self.onChanged(vobj, "Labels")

        elif prop == "OffsetY":
            self.onChanged(vobj, "Labels")

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        super().updateData(obj, prop)
        if prop == "Shape":
            line_coords, line_index = [], []
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