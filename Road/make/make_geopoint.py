# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create GeoPoint objects."""

import FreeCAD

from ..objects.geopoint import GeoPoint
from ..viewproviders.view_geopoint import ViewProviderGeoPoint

def create(name="GeoPoint", easting=0, northing=0, elevation=0, description=""):
    obj=FreeCAD.ActiveDocument.addObject("App::FeaturePython", "GeoPoint")

    GeoPoint(obj)
    ViewProviderGeoPoint(obj.ViewObject)

    obj.Label = name
    obj.Number = int(obj.Name[8:]) + 1 if obj.Name != "GeoPoint" else 1
    obj.Placement.Base = FreeCAD.Vector(easting, northing, elevation)
    obj.Description = description

    return obj