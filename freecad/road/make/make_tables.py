# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to get Table group."""

import FreeCAD

from ..objects.group import Group
from ..viewproviders.view_group import ViewProviderGroup

def create():
    """Factory method for Table group."""

    obj = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", "Tables")

    Group(obj, "Road::Tables")
    ViewProviderGroup(obj.ViewObject, "Tables")
    obj.Label = "Tables"

    return obj