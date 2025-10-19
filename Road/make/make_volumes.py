# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to get Volume group."""

import FreeCAD

from ..variables import icons_path
from ..objects.group import Group
from ..viewproviders.view_group import ViewProviderGroup

def create():
    """Factory method for Volume group."""

    obj = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", "Volumes")

    Group(obj, "Road::Volumes")
    ViewProviderGroup(obj.ViewObject, icons_path + "/Volumes.svg")
    obj.Label = "Volumes"

    return obj