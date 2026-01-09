# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Alignment objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_alignment
from ..tasks.task_alignment_editor import AlignmentEditor


class AlignmentCreate:
    """Command to create a new Alignment."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/AlignmentCreate.svg",
            "MenuText": "Create Alignment",
            "ToolTip": "Create Alignment geometry."}

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        # Check for selected object
        alignment = make_alignment.create()

        panel = AlignmentEditor(alignment)
        FreeCADGui.Control.showDialog(panel)

        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Alignment Create", AlignmentCreate())
