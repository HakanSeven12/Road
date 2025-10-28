# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Geolocation objects."""
import FreeCAD
from ..utils.get_group import georigin


class GeoObject:
    """This class is about GeoObject data features."""

    def __init__(self, obj):
        """Set data properties."""

        obj.addProperty(
            "App::PropertyPlacement", "Geolocation", "Base",
            "Placement").Geolocation = FreeCAD.Placement()

    def onChanged(self, obj, prop):
        """Do something when a data property has changed."""
        if prop == "Geolocation":
            origin = georigin(obj.Geolocation.Base)
            base = obj.Geolocation.Base.sub(origin.Base)
            if obj.Placement.Base != base:
                obj.Placement.Base = base

        if prop == "Placement":
            origin = georigin(obj.Geolocation.Base)
            base = obj.Placement.Base.add(origin.Base)
            if obj.Geolocation.Base != base:
                obj.Geolocation.Base = base