# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Structure objects."""
import FreeCAD
import Part
from .geo_object import GeoObject


class Structure(GeoObject):
    """This class is about Structure Object data features."""

    def __init__(self, obj):
        """Set data properties."""
        super().__init__(obj)

        self.Type = "Road::Structure"
        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""
        p1 = FreeCAD.Vector(-500, 0)
        p2 = FreeCAD.Vector(500, 0)
        p3 = FreeCAD.Vector(0, 2500)
        p4 = FreeCAD.Vector(0, -2500)

        horizontal = Part.Wire([Part.LineSegment(p1,p2).toShape()])
        vertical = Part.Wire([Part.LineSegment(p3,p4).toShape()])

        obj.Shape = Part.makeCompound([horizontal, vertical])