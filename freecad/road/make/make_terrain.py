# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create Terrain objects."""

import FreeCAD

from ..utils import get_group
from ..objects.terrain import Terrain
from ..viewproviders.view_terrain import ViewProviderTerrain

def create(clusters=[], label="Terrain"):
    obj=FreeCAD.ActiveDocument.addObject("Mesh::FeaturePython", "Terrain")

    Terrain(obj)
    ViewProviderTerrain(obj.ViewObject)

    obj.Label = label
    obj.Clusters = clusters
    
    terrains = get_group.get("Terrains")
    terrains.addObject(obj)

    return obj