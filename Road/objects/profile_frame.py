# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Profile Frame objects."""

import FreeCAD
import Part


class ProfileFrame:
    """This class is about Profile Frame Object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = "Road::ProfileFrame"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Alignment Shape").Shape = Part.Shape()

        obj.addProperty(
            "App::PropertyFloat", "Horizon", "Base",
            "Minimum elevation").Horizon = 0

        obj.addProperty(
            "App::PropertyFloat", "Length", "Geometry",
            "Offset length").Length = 1000

        obj.addProperty(
            "App::PropertyFloat", "Height", "Geometry",
            "Offset length").Height = 1000

        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""
        profiles = obj.getParentGroup()
        alignment = profiles.getParentGroup()

        z_values = []
        for profile in obj.Group:
            elevations = [item['Elevation'] for item in profile.Model.values()]
            z_values.extend([float(el) * 1000 for el in elevations if el != "None"])

        obj.Height = max(z_values) - min(z_values) if z_values else 1000
        obj.Horizon = min(z_values) if z_values else 0

        length = alignment.Length.Value
        obj.Length = length if length else 1000

        p1 = FreeCAD.Vector()
        p2 = FreeCAD.Vector(obj.Length, 0)
        p3 = FreeCAD.Vector(obj.Length, obj.Height)
        p4 = FreeCAD.Vector(0, obj.Height)

        shp = Part.makePolygon([p1,p2,p3,p4,p1])
        shp.Placement = obj.Placement
        obj.Shape = shp

    def onChanged(self, obj, prop):
        """Update Object when a property changed."""
        pass