# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to get Road workbench groups."""

import FreeCAD
import os
from .. import ICONPATH
from ..objects.group import Group
from ..viewproviders.view_group import ViewProviderGroup

from ..objects.coordinate_system import GeoOrigin
from ..viewproviders.view_georigin import ViewProviderGeoOrigin


def get(name):
    """Get the group."""
    obj = FreeCAD.ActiveDocument.getObject(name)
    if obj: return obj

    obj = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", name)

    Group(obj, "Road::" + name)
    ViewProviderGroup(obj.ViewObject, name)

    obj.Label = name
    return obj

def create_project(origin=FreeCAD.Vector()):
    """Get the GeoOrigin object"""
    obj = FreeCAD.ActiveDocument.getObject("CoordinateSystem")

    if not obj:
        obj=FreeCAD.ActiveDocument.addObject(
            "App::DocumentObjectGroupPython", "CoordinateSystem")
        obj.Label = "Coordinate System"

        GeoOrigin(obj, "Road::CoordinateSystem")
        ViewProviderGeoOrigin(
            obj.ViewObject, "CoordinateSystem")

        for group in ["Clusters", "Terrains", "Alignments", "GeoLines", "Structures", "Roads"]:
            obj.addObject(get(group))

    if origin.x == 0 or origin.y == 0:
        return obj

    if obj.Base == FreeCAD.Vector():
        origin.z = 0
        obj.Base = origin

    return obj