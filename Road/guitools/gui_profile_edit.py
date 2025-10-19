# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to edit Profile objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..tasks import task_profile_editor


class ProfileEdit:
    """Command to edit selected Profile."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/ProfileEdit.svg",
            "MenuText": "Edit Profile",
            "ToolTip": "Edit selected Profile geometry."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        for obj in FreeCADGui.Selection.getSelection():
            if obj.Proxy.Type == "Road::Profile":
                self.profile = obj
                return True
        return False

    def Activated(self):
        """Command activation method"""
        panel = task_profile_editor.run(self.profile)
        FreeCADGui.Control.showDialog(panel)

        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Profile Edit", ProfileEdit())
