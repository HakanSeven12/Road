# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create an Offset Alignment objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_alignment
from ..tasks.task_selection import SingleSelection


class AlignmentOffset:
    """Command to create an offset Alignment."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/AlignmentOffset.svg",
            "MenuText": "Create Offset Alignment",
            "ToolTip": "Create an Offset Alignment from another Alignment at a distance."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        self.parent_selector = SingleSelection(alignments)
        
        self.form = self.parent_selector
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        parent = self.parent_selector.selected_object

        alignment = make_alignment.create()
        alignment.Parent = parent
        alignment.OffsetLength = 5
        alignment.Model.coordinate_system.set_system('custom', alignment.Model.start_point, swap=True)
        #alignment.ViewObject.DisplayMode = "Offset"

        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Alignment Offset", AlignmentOffset())
