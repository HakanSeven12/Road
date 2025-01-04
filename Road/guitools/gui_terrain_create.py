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

"""Provides GUI tools to create Terrain objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_terrain


class CreateTerrain:
    """
    Command to create a new Terrain.
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
        return {
            'Pixmap': icons_path + '/TerrainCreate.svg',
            'MenuText': "Create Terrain",
            'ToolTip': "Create Terrain from selected point group(s)."
            }

    def IsActive(self):
        """
        Define tool button activation situation
        """
        # Check for document
        if FreeCAD.ActiveDocument:
            return True
        return False

    def Activated(self):
        """
        Command activation method
        """
        # Check for selected object
        terrain = make_terrain.create()
        selection = FreeCADGui.Selection.getSelection()

        if selection:
            clusters = terrain.Clusters.copy()

            for obj in selection:
                if obj.Proxy.Type == 'Road::Cluster':
                    clusters.append(obj)

            terrain.Clusters = clusters

        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand('Create Terrain', CreateTerrain())
