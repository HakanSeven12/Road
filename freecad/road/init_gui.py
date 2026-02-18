# SPDX-License-Identifier: LGPL-2.1-or-later

"""Initialization of the Road workbench (graphical interface)."""

import os
import FreeCAD, FreeCADGui
from . import ICONPATH


class RoadWorkbench(FreeCADGui.Workbench):
    """The Road Workbench definition."""

    MenuText = "Road"
    ToolTip = "The Road workbench is used for road design"
    Icon = os.path.join(ICONPATH, "RoadWorkbench.svg")

    def Initialize(self):
        """When the workbench is first loaded."""
        from . import tools

        # Set up command lists
        from .utils import init_tools as it
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
