# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create a Road objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_road
from ..tasks.task_selection import SingleSelection, SimpleComboBox


class RoadCreate:
    """Command to create a Road."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/RoadCreate.svg",
            "MenuText": "Create Road",
            "ToolTip": "Create a Road from alignment, profile and structure."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        structures = FreeCAD.ActiveDocument.getObject("Structures")

        self.alignment_selector = SingleSelection(alignments)
        self.profile_selector = SimpleComboBox(title="Select Profile")
        self.structure_selector = SingleSelection(structures)

        self.alignment_selector.combo_box.currentTextChanged.connect(self.profile_update)
        self.profile_update()

        self.form = [self.alignment_selector, self.profile_selector, self.structure_selector]
        FreeCADGui.Control.showDialog(self)

    def profile_update(self):
        """Update profile selector when alignment changes"""
        alignment = self.alignment_selector.selected_object
        profiles = alignment.Model.profiles
        profile_names = profiles.get_profalign_names()
        self.profile_selector.update_items(profile_names)

    def accept(self):
        """Panel 'OK' button clicked"""
        alignment = self.alignment_selector.selected_object
        selected_profile_name = self.profile_selector.selected_item
        structure = self.structure_selector.selected_object

        road = make_road.create()

        road.Alignment = alignment
        road.Profile = selected_profile_name
        road.Structure = structure

        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.Control.closeDialog()


FreeCADGui.addCommand("Road Create", RoadCreate())
