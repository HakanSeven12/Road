# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to get Region group."""

import FreeCAD

from ..variables import icons_path
from ..objects.group import Group
from ..viewproviders.view_group import ViewProviderGroup

def create():
    """Factory method for Region group."""

    obj = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", "Regions")

    Group(obj, "Road::Regions")
    ViewProviderGroup(obj.ViewObject, icons_path + "/Regions.svg")

    obj.Label = "Regions"

    return obj