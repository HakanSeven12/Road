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
        self.editor = ProfileEditor(profile=self.profile_frame)

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
        if alignment and alignment.Model.get_profile():
            profiles = alignment.Model.get_profile()
            profile_names = profiles.get_profalign_names()
            self.profile_selector.update_items(profile_names)
            # Trigger editor update with new profile
            self.editor_update()

    def editor_update(self):
        """Update editor when profile selection changes"""
        if not self.editor:
            return
        
        alignment = self.alignment_selector.selected_object
        if not alignment:
            return
        
        profile = alignment.Model.get_profile()
        if not profile:
            return
        
        selected_profile_name = self.profile_selector.selected_item
        
        # Find the selected profalign
        selected_profalign = None
        for profalign in profile.profalign_list:
            if profalign['name'] == selected_profile_name:
                selected_profalign = profalign
                break
        
        if not selected_profalign:
            return
        
        # Update editor's PVI data
        if 'geometry' in selected_profalign:
            # Extract PVI points from geometry
            pvi_list = []
            for geom in selected_profalign['geometry']:
                if 'pvi' in geom:
                    pvi_data = {
                        'station': geom['pvi']['station'],
                        'elevation': geom['pvi']['elevation'],
                        'curve_length': geom.get('length', None),
                        'curve_type': geom.get('Type', 'ParaCurve'),
                        'description': geom.get('desc', '')
                    }
                    pvi_list.append(pvi_data)
            
            # Update editor's pvi_data and reload
            self.editor.pvi_data = pvi_list
            self.editor.load_data()

FreeCADGui.addCommand("Profile Edit", ProfileEdit())