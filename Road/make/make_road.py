# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create Road objects."""

import FreeCAD

from ..utils import get_group
from ..objects.road import Road
from ..viewproviders.view_road import ViewProviderRoad

def create(name="Road"):
    obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Road")

    Road(obj)
    ViewProviderRoad(obj.ViewObject)

    obj.Label = name

    group = get_group.get("Roads")
    group.addObject(obj)

    return obj