# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to get Sections object."""

import FreeCAD

from ..variables import icons_path
from ..objects.group import Group
from ..viewproviders.view_group import ViewProviderGroup

def create():
    """Factory method for Section group."""

    obj = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", "Sections")

    Group(obj, "Road::Sections")
    ViewProviderGroup(obj.ViewObject, icons_path + "/CreateSections.svg")
    obj.Label = "Sections"

    return obj