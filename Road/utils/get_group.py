# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2025 Hakan Seven <hakanseven12@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

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

    if obj:
        if obj.Base == FreeCAD.Vector():
            origin.z = 0
            obj.Base = origin
        return obj

    obj=FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", name)

    GeoOrigin(obj, "Road::" + name)
    ViewProviderGeoOrigin(
        obj.ViewObject, icons_path + "/" + name + ".svg")

    origin.z = 0
    obj.Base = origin

    for group in ["Clusters", "Terrains", "Alignments", "GeoLines"]:
        obj.addObject(get(group))

    FreeCAD.ActiveDocument.recompute()
    return obj