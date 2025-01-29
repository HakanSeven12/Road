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

"""Provides GUI tools to create Profile objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_profile
from ..tasks import task_profile_editor


class ProfileCreate:
    """Command to create a new Profile."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/ProfileCreate.svg",
            "MenuText": "Create Profile",
            "ToolTip": "Create Profile for selected Profile Frame."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        if FreeCAD.ActiveDocument:
            # Check for selected object
            selection = FreeCADGui.Selection.getSelection()
            if selection:
                if selection[-1].Proxy.Type == "Road::ProfileFrame":
                    self.profile_frame = selection[-1]
                    return True
        return False

    def Activated(self):
        """Command activation method"""
        profile = make_profile.create()
        self.profile_frame.addObject(profile)

        panel = task_profile_editor.run(profile)
        FreeCADGui.Control.showDialog(panel)

        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Profile Create", ProfileCreate())
