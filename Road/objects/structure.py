# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Structure objects."""
import FreeCAD
import Part


class Structure:
    """This class is about Structure Object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = "Road::Structure"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Alignment Shape").Shape = Part.makeCompound([])

        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""
        p1 = FreeCAD.Vector(-500, 0)
        p2 = FreeCAD.Vector(500, 0)
        p3 = FreeCAD.Vector(0, 2500)
        p4 = FreeCAD.Vector(0, -2500)

        horizontal = Part.Wire([Part.LineSegment(p1,p2).toShape()])
        vertical = Part.Wire([Part.LineSegment(p3,p4).toShape()])

        shp = Part.makeCompound([horizontal, vertical])
        shp.Placement = obj.Placement
        obj.Shape = shp