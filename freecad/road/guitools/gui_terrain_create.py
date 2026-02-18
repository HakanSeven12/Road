# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Terrain objects."""

import FreeCAD, FreeCADGui
import os
from .. import ICONPATH
from ..make import make_terrain
from ..tasks.task_selection import MultipleSelection


class TerrainCreate:
    """Command to create a new Terrain."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "TerrainCreate.svg"),
            "MenuText": "Create Terrain",
            "ToolTip": "Create Terrain from selected point group(s)."
            }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        clusters = FreeCAD.ActiveDocument.getObject("Clusters")
        self.cluster_selector = MultipleSelection(clusters)

        self.form = self.cluster_selector
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        clusters = self.cluster_selector.selected_objects
        terrain = make_terrain.create()
        terrain.Clusters = clusters

        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Create Terrain", TerrainCreate())
