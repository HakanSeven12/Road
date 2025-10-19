# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to get Structure object."""

import FreeCAD

from ..variables import icons_path
from ..objects.structure import Structure
from ..viewproviders.view_structure import ViewProviderStructure

def create():
    """Factory method for Region group."""
    obj = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", "Structure")

    Structure(obj)
    ViewProviderStructure(obj.ViewObject)

    return obj