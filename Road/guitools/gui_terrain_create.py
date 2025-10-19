# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Terrain objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_terrain
from ..tasks.task_selection import MultipleSelection


class TerrainCreate:
    """Command to create a new Terrain."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/TerrainCreate.svg",
            "MenuText": "Create Terrain",
            "ToolTip": "Create Terrain from selected point group(s)."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        clusters = FreeCAD.ActiveDocument.getObject("Clusters")
        self.cluster_selector = MultipleSelection(clusters)

        self.form = self.cluster_selector
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        """Panel 'OK' button clicked"""
        clusters = self.cluster_selector.selected_objects
        terrain = make_terrain.create()
        terrain.Clusters = clusters

        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Create Terrain", TerrainCreate())
