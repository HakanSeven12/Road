# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to get Component object."""

import FreeCAD
from ..objects.component import Component
from ..viewproviders.view_group import ViewProviderGroup

def create():
    """Factory method for Region group."""
    obj = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", "Component")

    Component(obj)
    ViewProviderGroup(obj.ViewObject, "Component.svg")

    return obj