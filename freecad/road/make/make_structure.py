# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to get Structure object."""

import FreeCAD

from ..utils import get_group
from ..objects.structure import Structure
from ..viewproviders.view_structure import ViewProviderStructure

def create():
    """Factory method for Region group."""
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Structure")
    obj.addExtension("App::GroupExtensionPython")
    obj.ViewObject.addExtension("Gui::ViewProviderGroupExtensionPython")

    Structure(obj)
    ViewProviderStructure(obj.ViewObject)

    group = get_group.get("Structures")
    group.addObject(obj)

    return obj