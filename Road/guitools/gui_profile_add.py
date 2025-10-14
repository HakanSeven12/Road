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

"""Provides GUI tools to add Terrain Profile objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_profile
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
        FreeCADGui.Control.closeDialog()

        for i in self.terrains:
            profile = make_profile.create()
            self.profile_frame.addObject(profile)
            profile.ViewObject.DisplayMode = "Terrain"
            profile.Terrain = i

FreeCADGui.addCommand("Profile Add", ProfileAdd())
