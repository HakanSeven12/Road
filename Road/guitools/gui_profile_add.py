# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to add Terrain Profile objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..tasks.task_selection import MultipleSelection


class ProfileAdd:
    """Command to add Terrain Profile."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/ProfileAdd.svg",
            "MenuText": "Add Terrain Profile",
            "ToolTip": "Add Terrain Profile to the selected Profile Frame."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        for obj in FreeCADGui.Selection.getSelection():
            if obj.Proxy.Type == "Road::ProfileFrame":
                self.profile_frame = obj
                return True
        return False

    def Activated(self):
        """Command activation method"""
        terrains = FreeCAD.ActiveDocument.getObject("Terrains")
        self.terrain_selector = MultipleSelection(terrains)

        self.form = self.terrain_selector
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        """Panel 'OK' button clicked"""
        self.terrains = self.terrain_selector.selected_objects
        self.profile_frame.Terrains = self.terrains

        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Profile Add", ProfileAdd())
