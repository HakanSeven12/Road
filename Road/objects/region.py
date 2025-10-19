# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Region objects."""
import FreeCAD

import Part

import copy


class Region:
    """This class is about Region object data features."""

    def __init__(self, obj):
        """Set data properties."""
        self.Type = "Road::Region"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Object shape").Shape = Part.Shape()

        obj.addProperty(
            "App::PropertyBool", "AtHorizontalGeometry", "Base",
            "Show/hide labels").AtHorizontalGeometry = True

        obj.addProperty(
            "App::PropertyPythonObject", "Stations", "Base",
            "List of stations").Stations = {}

        obj.addProperty(
            "App::PropertyBool", "FromAlignmentStart", "Region",
            "Show/hide labels").FromAlignmentStart = True

        obj.addProperty(
            "App::PropertyBool", "ToAlignmentEnd", "Region",
            "Show/hide labels").ToAlignmentEnd = True

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

        self.onChanged(obj,'FromAlignmentStart')
        self.onChanged(obj,'ToAlignmentEnd')

        obj.Proxy = self

    def execute(self, obj):
        """
        Do something when doing a recomputation.
        """

        """
        start = obj.getPropertyByName("StartStation")
        end = obj.getPropertyByName("EndStation")
        """

        regions = obj.getParentGroup()
        alignment = regions.getParentGroup()

        if not hasattr(alignment.Proxy, "model"): return

        tangent = obj.IncrementAlongTangents
        curve = obj.IncrementAlongCurves
        spiral = obj.IncrementAlongSpirals
        terminal = obj.AtHorizontalGeometry

        model = alignment.Proxy.model
        stations = model.get_stations([tangent, curve, spiral], terminal)

        lines = []
        # Computing coordinates and orthoginals for guidelines
        for sta in stations:
            tuple_coord, tuple_vec = model.get_orthogonal( sta/1000, "Left")
            coord = FreeCAD.Vector(tuple_coord)
            vec = FreeCAD.Vector(tuple_vec)
            left_vec = copy.deepcopy(vec)
            right_vec = copy.deepcopy(vec)
            left_side = coord.add(left_vec.multiply(obj.LeftOffset*1000))
            right_side = coord.add(right_vec.negative().multiply(obj.RightOffset*1000))
            
            lines.append(Part.makePolygon([left_side, coord, right_side]))
        obj.Shape = Part.makeCompound(lines)

    def onChanged(self, obj, prop):
        """
        Do something when a data property has changed.
        """
        regions = obj.getParentGroup()
        if not regions: return
        alignment = regions.getParentGroup()

        if prop == "Group":
            obj.Placement = alignment.Placement if alignment else FreeCAD.Placement()

        if prop == "FromAlignmentStart":
            if obj.getPropertyByName(prop):
                obj.setEditorMode('StartStation', 1)
                obj.StartStation = alignment.StartStation
            else:
                obj.setEditorMode('StartStation', 0)

        if prop == "ToAlignmentEnd":
            if obj.getPropertyByName(prop):
                obj.setEditorMode('EndStation', 1)
                obj.EndStation = alignment.EndStation
            else:
                obj.setEditorMode('EndStation', 0)
