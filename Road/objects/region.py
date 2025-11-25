# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Region objects."""
import FreeCAD, Part
from .geo_object import GeoObject
from ..utils.support import  zero_reference


class Region(GeoObject):
    """This class is about Region object data features."""

    def __init__(self, obj):
        """Set data properties."""
        super().__init__(obj)

        self.Type = "Road::Region"

        obj.addProperty(
            "App::PropertyBool", "AtHorizontalGeometry", "Base",
            "Add stations at geometry transitions").AtHorizontalGeometry = True

        obj.addProperty(
            "App::PropertyPythonObject", "Stations", "Base",
            "List of stations").Stations = []

        obj.addProperty(
            "App::PropertyBool", "FromAlignmentStart", "Region",
            "Start from alignment beginning").FromAlignmentStart = True

        obj.addProperty(
            "App::PropertyBool", "ToAlignmentEnd", "Region",
            "End at alignment end").ToAlignmentEnd = True

        obj.addProperty(
            "App::PropertyLength", "StartStation", "Station",
            "Guide lines start station").StartStation = 0

        obj.addProperty(
            "App::PropertyLength", "EndStation", "Station",
            "Guide lines end station").EndStation = 0

        obj.addProperty(
            "App::PropertyFloat", "IncrementAlongTangents", "Increment",
            "Distance between guide lines along tangents").IncrementAlongTangents = 10

        obj.addProperty(
            "App::PropertyFloat", "IncrementAlongCurves", "Increment",
            "Distance between guide lines along curves").IncrementAlongCurves = 10

        obj.addProperty(
            "App::PropertyFloat", "IncrementAlongSpirals", "Increment",
            "Distance between guide lines along spirals").IncrementAlongSpirals = 10

        obj.addProperty(
            "App::PropertyFloat", "RightOffset", "Offset",
            "Length of right offset").RightOffset = 20

        obj.addProperty(
            "App::PropertyFloat", "LeftOffset", "Offset",
            "Length of left offset").LeftOffset = 20

        obj.setEditorMode('StartStation', 1)
        obj.setEditorMode('EndStation', 1)

        self.onChanged(obj, 'FromAlignmentStart')
        self.onChanged(obj, 'ToAlignmentEnd')

        obj.Proxy = self

    def execute(self, obj):
        """
        Do something when doing a recomputation.
        """
        regions = obj.getParentGroup()
        if not regions:
            return
            
        alignment = regions.getParentGroup()
        if not alignment:
            return

        # Get alignment model
        alignment_model = alignment.Model
        
        # Convert stations from FreeCAD units (mm) to alignment units (m)
        start = obj.StartStation.Value / 1000.0
        end = obj.EndStation.Value / 1000.0
        
        # Prepare increment dictionary for different element types
        increments = {
            'Line': obj.IncrementAlongTangents,
            'Curve': obj.IncrementAlongCurves,
            'Spiral': obj.IncrementAlongSpirals
        }
        
        at_geometry = obj.AtHorizontalGeometry

        # Generate stations using alignment model method
        try:
            stations = alignment_model.generate_stations(
                start_station=start,
                end_station=end,
                increments=increments,
                at_geometry_points=at_geometry
            )
        except AttributeError:
            FreeCAD.Console.PrintError(
                "Error: Alignment model does not have generate_stations method. "
                "Please update alignment.py\n"
            )
            return
        
        # Store stations in mm for compatibility
        obj.Stations = [sta * 1000.0 for sta in stations]

        lines = []
        # Computing coordinates and orthogonals for guidelines
        for sta in stations:
            try:
                # Small tolerance for floating point errors
                tolerance = 1e-6
                
                # Clamp station to alignment range
                align_start = alignment_model.get_sta_start()
                align_end = alignment_model.get_sta_end()
                
                clamped_sta = max(align_start, min(sta, align_end - tolerance))
                
                # Get point and orthogonal vector using new model API
                tuple_coord, tuple_vec = alignment_model.get_orthogonal_at_station(
                    clamped_sta, "left"
                )
                
                coord = zero_reference(alignment_model.get_start_point(), [tuple_coord])
                left_vec = FreeCAD.Vector(*tuple_vec)
                right_vec = FreeCAD.Vector(*tuple_vec).negative()
                
                # Calculate offset points
                left_side = coord[0].add(left_vec.multiply(obj.LeftOffset * 1000))
                right_side = coord[0].add(right_vec.multiply(obj.RightOffset * 1000))
                
                lines.append(Part.makePolygon([left_side, coord, right_side]))
                
            except (ValueError, AttributeError) as e:
                # Skip stations that cause errors (outside alignment range, etc.)
                FreeCAD.Console.PrintWarning(
                    f"Warning: Could not generate guideline at station {sta}: {str(e)}\n"
                )
                continue
        
        if lines:
            obj.Shape = Part.makeCompound(lines)
        else:
            obj.Shape = Part.Shape()

    def onChanged(self, obj, prop):
        """Do something when a data property has changed."""
        super().onChanged(obj, prop)
        
        regions = obj.getParentGroup()
        if not regions:
            return
            
        alignment = regions.getParentGroup()
        if not alignment:
            return

        if prop == "Group":
            obj.Placement = alignment.Placement if alignment else FreeCAD.Placement()

        if prop == "FromAlignmentStart":
            if obj.getPropertyByName(prop):
                obj.setEditorMode('StartStation', 1)
                if hasattr(alignment, 'StartStation'):
                    obj.StartStation = alignment.StartStation
            else:
                obj.setEditorMode('StartStation', 0)

        if prop == "ToAlignmentEnd":
            if obj.getPropertyByName(prop):
                obj.setEditorMode('EndStation', 1)
                if hasattr(alignment, 'EndStation'):
                    obj.EndStation = alignment.EndStation
            else:
                obj.setEditorMode('EndStation', 0)