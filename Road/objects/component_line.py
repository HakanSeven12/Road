# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Component Line objects."""
import Part
from .geo_object import GeoObject


class ComponentLine(GeoObject):
    """This class is about Component Line Object data features."""

    def __init__(self, obj):
        """Set data properties."""
        super().__init__(obj)

        self.Type = "Road::ComponentLine"

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
            obj.Placement = obj.Start.Placement
            start = obj.Start.Placement.Base - obj.Placement.Base
            end = obj.End.Placement.Base - obj.Placement.Base
            obj.Shape = Part.makeLine(start, end)