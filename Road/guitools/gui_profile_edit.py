# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to edit Profile objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..tasks.task_profile_editor import ProfileEditor
from ..tasks.task_selection import SingleSelection, SimpleComboBox

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
            if obj.Proxy.Type == "Road::ProfileFrame":
                self.profile_frame = obj
                return True
        return False

    def Activated(self):
        """Command activation method"""
        profiles = self.profile_frame.getParentGroup()
        alignment = profiles.getParentGroup()
        self.form = ProfileEditor(alignment)
        FreeCADGui.Control.showDialog(self)

    def needsFullSpace(self):
        return True
    
FreeCADGui.addCommand("Profile Edit", ProfileEdit())