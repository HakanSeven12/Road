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

"""Initialization of the Road workbench (graphical interface)."""

import os

import FreeCAD, FreeCADGui


__title__ = "FreeCAD Road Workbench - Init file"
__author__ = "Hakan Seven <hakanseven12@gmail.com>"
__url__ = "https://www.freecad.org"

class RoadWorkbench(FreeCADGui.Workbench):
    """The Road Workbench definition."""

    def __init__(self):
        __dirname__ = os.path.join(FreeCAD.getUserAppDataDir(), "Mod", "Road", "Road")
        self.__class__.Icon = os.path.join(__dirname__,
                                           "resources","icons",
                                           "RoadWorkbench.svg")

        self.__class__.MenuText = "Road"
        self.__class__.ToolTip = "The Road workbench is used for road design"

    def Initialize(self):
        """When the workbench is first loaded."""
        import Road.tools

        # Set up command lists
        import Road.utils.init_tools as it
        self.point_commands = it.get_point_commands()
        self.surface_commands = it.get_surface_commands()
        self.alignment_commands = it.get_alignment_commands()
        self.road_commands = it.get_road_commands()
        self.section_commands = it.get_section_commands()
        self.line3D_commands = it.get_geoline_commands()
        self.io_commands = it.get_io_commands()

        # Set up toolbars
        it.init_toolbar(self,
                        "GeoPoint",
                        self.point_commands)
        it.init_toolbar(self,
                        "Terrain",
                        self.surface_commands)
        it.init_toolbar(self,
                        "Alignment",
                        self.alignment_commands)
        it.init_toolbar(self,
                        "Road",
                        self.road_commands)
        it.init_toolbar(self,
                        "Section",
                        self.section_commands)
        it.init_toolbar(self,
                        "GeoLine",
                        self.line3D_commands)
        it.init_toolbar(self,
                        "Input-Output",
                        self.io_commands)

        """
        # Set up menus
        it.init_menu(self,
                    "Input-Output tools",
                    self.io_commands)
        """

    def Activated(self):
        """When entering the workbench."""
        FreeCAD.Console.PrintLog("Road workbench activated.\n")

    def Deactivated(self):
        """When quitting the workbench."""
        FreeCAD.Console.PrintLog("Road workbench deactivated.\n")

    def ContextMenu(self, recipient):
        """Define an optional custom context menu."""
        selection = FreeCADGui.Selection.getSelection()
        if len(selection) == 1:
            if selection[0].Proxy.Type == 'Road::Terrain':
                self.appendContextMenu("Edit surface", self.surface_commands)

    def GetClassName(self):
        """Type of workbench."""
        return 'Gui::PythonWorkbench'


FreeCADGui.addWorkbench(RoadWorkbench())
