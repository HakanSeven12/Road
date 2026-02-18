# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to get Profile group."""

import FreeCAD
from ..objects.group import Group
from ..viewproviders.view_group import ViewProviderGroup

def create():
    """Factory method for Profile group."""

    obj = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", "Profiles")

    Group(obj, "Road::Profiles")
    ViewProviderGroup(obj.ViewObject, "Profiles")
    obj.Label = "Profiles"

    return obj