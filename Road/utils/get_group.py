# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to get Road workbench groups."""

import FreeCAD

from ..variables import icons_path
from ..objects.group import Group
from ..viewproviders.view_group import ViewProviderGroup

from ..objects.georigin import GeoOrigin
from ..viewproviders.view_georigin import ViewProviderGeoOrigin


def get(name):
    """Get the group."""
    obj = FreeCAD.ActiveDocument.getObject(name)
    if obj: return obj

    obj = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", name)

    Group(obj, "Road::" + name)
    ViewProviderGroup(
        obj.ViewObject, icons_path + "/" + name + ".svg")

    obj.Label = name
    return obj

def georigin(origin=FreeCAD.Vector(), name = "GeoOrigin"):
    """Get the GeoOrigin object"""
    obj = FreeCAD.ActiveDocument.getObject(name)

    if not obj:
        obj=FreeCAD.ActiveDocument.addObject(
            "App::DocumentObjectGroupPython", name)

        GeoOrigin(obj, "Road::" + name)
        ViewProviderGeoOrigin(
            obj.ViewObject, icons_path + "/" + name + ".svg")

        for group in ["Clusters", "Terrains", "Alignments", "GeoLines", "Structures", "Roads"]:
            obj.addObject(get(group))

    if origin.x == 0 or origin.y == 0:
        return obj

    if obj.Base == FreeCAD.Vector():
        origin.z = 0
        obj.Base = origin

    FreeCAD.ActiveDocument.recompute()
    return obj