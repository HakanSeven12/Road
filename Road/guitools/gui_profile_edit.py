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
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        self.alignment_selector = SingleSelection(alignments)
        self.profile_selector = SimpleComboBox(title="Select Profile")
        self.editor = ProfileEditor()

        self.alignment_selector.combo_box.currentTextChanged.connect(self.profile_update)
        self.profile_selector.combo_box.currentTextChanged.connect(self.editor_update)
        self.profile_update()
        self.editor_update()
        
        self.form = [self.alignment_selector, self.profile_selector, self.editor]
        FreeCADGui.Control.showDialog(self)

        FreeCAD.ActiveDocument.recompute()

    def profile_update(self):
        """Update profile selector when alignment changes"""
        alignment = self.alignment_selector.selected_object
        profiles = alignment.Model.profiles
        profile_names = profiles.get_profalign_names()
        self.profile_selector.update_items(profile_names)
        # Trigger editor update with new profile
        self.editor_update()

    def editor_update(self):
        """Update editor when profile selection changes"""
        alignment = self.alignment_selector.selected_object
        selected_profile_name = self.profile_selector.selected_item

        profiles = alignment.Model.profiles
        selected_profalign = profiles.get_profile_by_name(selected_profile_name)
        
        # Update editor's PVI data
        if  selected_profalign:
            self.editor.load_data(selected_profalign)

    def needsFullSpace(self):
        return True
    
FreeCADGui.addCommand("Profile Edit", ProfileEdit())