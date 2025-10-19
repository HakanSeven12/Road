# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create Component Shape objects."""

import FreeCAD

from ..objects.component_shape import ComponentShape
from ..viewproviders.view_component_shape import ViewProviderComponentShape

def create(label="Shape"):
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "ComponentShape")

    ComponentShape(obj)
    ViewProviderComponentShape(obj.ViewObject)
    obj.Label = label

    return obj