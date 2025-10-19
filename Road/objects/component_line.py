# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Component Line objects."""
import FreeCAD
import Part


class ComponentLine:
    """This class is about Component Line Object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = "Road::ComponentLine"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Alignment Shape").Shape = Part.Shape()

        obj.addProperty(
            "App::PropertyLink", "Start", "Geometry",
            "Start point of line.")

        obj.addProperty(
            "App::PropertyLink", "End", "Geometry",
            "End point of line.")

        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""
        if obj.Start and obj.End:
            placement = FreeCAD.Placement()
            placement.move(obj.Start.Placement.Base)
            obj.Placement = placement

            start = obj.Placement.Base
            end = obj.End.Placement.Base
            obj.Shape = Part.makeLine(start, end)