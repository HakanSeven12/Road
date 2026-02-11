# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create GeoPoint objects."""

import FreeCAD

from ..utils import get_group
from ..objects.geopoints import GeoPoints
from ..viewproviders.view_geopoints import ViewProviderGeoPoints

def create(name="GeoPoints"):
    obj=FreeCAD.ActiveDocument.addObject("Points::FeaturePython", "GeoPoints")

    GeoPoints(obj)
    ViewProviderGeoPoints(obj.ViewObject)

    obj.Label = name

    clusters = get_group.get("Clusters")
    clusters.addObject(obj)
    
    return obj