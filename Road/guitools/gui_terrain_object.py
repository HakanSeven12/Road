# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2025 Hakan Seven <hakanseven12@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""Provides GUI tools to add object to Terrain objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..tasks import task_set_prop
from ..utils import get_group
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
        """
        Command activation method
        """
        terrain = FreeCADGui.Selection.getSelection()[0]
        clusters = get_group.get("Clusters")
        panel = task_set_prop.TaskSetProperty(terrain, "Clusters", clusters)
        FreeCADGui.Control.showDialog(panel)
        
        FreeCAD.ActiveDocument.recompute()

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