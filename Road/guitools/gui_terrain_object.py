# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to add object to Terrain objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..tasks.task_selection import MultipleSelection


class TerrainAddCluster:
    """Command to add a cluster to Terrain."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {"Pixmap": icons_path + "/TerrainAddCluster.svg",
            "MenuText": "Add Cluster",
            "ToolTip": "Add a cluster to selected Terrain."}

    def IsActive(self):
        """Define tool button activation situation"""
        return True

    def Activated(self):
        """Command activation method"""
        self.terrain = FreeCADGui.Selection.getSelection()[0]
        clusters = FreeCAD.ActiveDocument.getObject("Clusters")
        self.cluster_selector = MultipleSelection(clusters)

        self.form = self.cluster_selector
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        """Panel 'OK' button clicked"""
        clusters = self.cluster_selector.selected_objects
        self.terrain.Clusters = clusters

        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()

class TerrainObjectGroup:
    """Gui Command group for the Arc tools."""

    def GetResources(self):
        """Set icon, menu and tooltip."""
        return {"Pixmap": icons_path + "/TerrainObject.svg",
                "MenuText": "Add Object",
                "ToolTip": "Add object to selected Terrain."}

    def GetCommands(self):
        """Return a tuple of commands in the group."""
        return ("Terrain Add Cluster",
                "Terrain Add Cluster")

    def IsActive(self):
        """Return True when this command should be available."""
        if FreeCAD.ActiveDocument:
            selection = FreeCADGui.Selection.getSelection()
            if selection:
                if selection[-1].Proxy.Type == "Road::Terrain":
                    return True
        return False


FreeCADGui.addCommand("Terrain Add Cluster", TerrainAddCluster())
FreeCADGui.addCommand("Terrain Object", TerrainObjectGroup())