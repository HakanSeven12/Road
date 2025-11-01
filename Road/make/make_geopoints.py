# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create GeoPoint objects."""

import FreeCAD

from ..utils import get_group
from ..objects.geopoints import GeoPoints
from ..viewproviders.view_geopoints import ViewProviderGeoPoints

def create(name="GeoPoints"):
    clusters = get_group.get("Clusters")
    obj=FreeCAD.ActiveDocument.addObject("Points::FeaturePython", "GeoPoints")
    clusters.addObject(obj)

    GeoPoints(obj)
    ViewProviderGeoPoints(obj.ViewObject)

    obj.Label = name
    return obj