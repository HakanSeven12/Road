# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create Component Point objects."""

import FreeCAD

from ..objects.component_point import ComponentPoint
from ..viewproviders.view_component_point import ViewProviderComponentPoint

def create(label="Point"):
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "ComponentPoint")

    ComponentPoint(obj)
    ViewProviderComponentPoint(obj.ViewObject)
    obj.Label = label

    return obj