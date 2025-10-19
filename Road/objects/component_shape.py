# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Component Shape objects."""
import FreeCAD
import Part


class ComponentShape:
    """This class is about Component Shape Object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = "Road::ComponentShape"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Alignment Shape").Shape = Part.Shape()

        obj.addProperty(
            "App::PropertyLinkList", "Lines", "Geometry",
            "Lines of Shape.")

        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""
        component = obj.getParentGroup()
        structure = component.getParentGroup()
        obj.Placement = structure.Placement
        
        edges = [line.Shape for line in obj.Lines]
        sorted = Part.sortEdges(edges)
        if not sorted: return
        wire = Part.Wire(sorted[0])
        if wire.isClosed():
            obj.Shape = Part.Face(wire)