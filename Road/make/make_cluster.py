# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create Cluster objects."""

import FreeCAD

from ..utils import get_group
from ..variables import icons_path
from ..objects.group import Group
from ..viewproviders.view_group import ViewProviderGroup

def create(label="Cluster"):
    obj = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", "Cluster")

    Group(obj, "Road::Cluster")
    ViewProviderGroup(obj.ViewObject, icons_path + '/Cluster.svg')
    obj.Label = label

    clusters = get_group.get("Clusters")
    clusters.addObject(obj)


    return obj