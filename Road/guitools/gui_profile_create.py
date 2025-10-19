# SPDX-License-Identifier: LGPL-2.1-or-later

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
        for obj in FreeCADGui.Selection.getSelection():
            if obj.Proxy.Type == "Road::ProfileFrame":
                self.profile_frame = obj
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
