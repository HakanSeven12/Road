# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create Component Line objects."""

import FreeCAD

from ..objects.component_line import ComponentLine
from ..viewproviders.view_component_line import ViewProviderComponentLine

def create(label="L"):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "ComponentLine")

    ComponentLine(obj)
    ViewProviderComponentLine(obj.ViewObject)
    obj.Label = label

    return obj