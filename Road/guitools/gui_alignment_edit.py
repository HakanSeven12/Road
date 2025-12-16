# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to edit Alignment objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..tasks.task_alignment_editor import AlignmentEditor


class AlignmentEdit:
    """Command to edit selected Alignment geometry."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/AlignmentEdit.svg",
            "MenuText": "Edit Alignment",
            "ToolTip": "Edit selected Alignment geometry."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        for obj in FreeCADGui.Selection.getSelection():
            if obj.Proxy.Type == "Road::Alignment":
                self.alignment = obj
                return True
        return False

    def Activated(self):
        """Command activation method"""
        panel = AlignmentEditor(self.alignment)
        FreeCADGui.Control.showDialog(panel)

        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Alignment Edit", AlignmentEdit())
