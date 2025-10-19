# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Region objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_region
from ..tasks.task_selection import SingleSelection


class RegionCreate:
    """Command to create a new Region object for selected alignment"""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/RegionCreate.svg",
            "MenuText": "Create Region",
            "ToolTip": "Create Region lines at stations along an alignment"
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        self.alignment_selector = SingleSelection(alignments)

        self.form = self.alignment_selector
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        """Panel 'OK' button clicked"""
        alignment = self.alignment_selector.selected_object
        make_region.create(alignment)
        
        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("Region Create", RegionCreate())
