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

"""Provides GUI tools to add data to Terrain objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..tasks import task_set_prop
from ..utils import get_group


class AddCluster:
    """
    Command to add a point to Terrain.
    """

    def __init__(self):
        """
        Constructor
        """
        pass

    def GetResources(self):
        """
        Return the command resources dictionary
        """
        return {'Pixmap': icons_path + '/AddTriangle.svg',
            'MenuText': "Add Cluster",
            'ToolTip': "Add a cluster to selected Terrain."}

    def IsActive(self):
        """
        Define tool button activation situation
        """
        # Check for document
        if FreeCAD.ActiveDocument:
            # Check for selected object
            selection = FreeCADGui.Selection.getSelection()
            if len(selection)==1:
                if selection[0].Proxy.Type == 'Road::Terrain':
                    self.terrain = selection[0]
                    return True
        return False

    def Activated(self):
        """
        Command activation method
        """
        clusters = get_group.get("Clusters")
        panel = task_set_prop.TaskSetProperty(self.terrain, "Clusters", clusters)
        FreeCADGui.Control.showDialog(panel)
        
        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand('Add Cluster', AddCluster())


class TerrainDataGroup:
    """Gui Command group for the Arc tools."""

    def GetResources(self):
        """Set icon, menu and tooltip."""
        return {'Pixmap': icons_path + '/TerrainData.svg',
                "MenuText": "Add Data",
                "ToolTip": "Add data to surfaces."}

    def GetCommands(self):
        """Return a tuple of commands in the group."""
        return ('Import Points',
                'Add Cluster')

    def IsActive(self):
        """Return True when this command should be available."""
        return bool(FreeCADGui.ActiveDocument)


FreeCADGui.addCommand('Terrain Data', TerrainDataGroup())