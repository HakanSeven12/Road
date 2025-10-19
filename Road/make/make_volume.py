# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create Volume objects."""

import FreeCAD

from ..objects.volume import Volume
from ..viewproviders.view_volume import ViewProviderVolume

def create(region, name='Volume'):
    obj=FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Volume")

    for item in region.Group:
        if item.Proxy.Type == 'Road::Volumes':
            item.addObject(obj)
            break

    Volume(obj)
    ViewProviderVolume(obj.ViewObject)

    obj.Label = name

    return obj