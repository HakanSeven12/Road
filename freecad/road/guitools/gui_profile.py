# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to Profile commands."""

import FreeCAD, FreeCADGui
import os
from .. import ICONPATH
from ..make import make_profile_frame
from ..utils.trackers import ViewTracker
from ..tasks.task_profile_editor import ProfileEditor
from ..tasks.task_selection import SingleSelection, MultipleSelection


class ProfileFrameCreate:
    """Command to create a Profile Frame."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "ProfileFrameCreate.svg"),
            "MenuText": "Create Profile Frame",
            "ToolTip": "Create a Profile Frame for selected Alignment."
            }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        self.alignment_selector = SingleSelection(alignments)

        terrains = FreeCAD.ActiveDocument.getObject("Terrains")
        self.terrain_selector = MultipleSelection(terrains)

        self.form = [self.alignment_selector, self.terrain_selector]
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        FreeCAD.Console.PrintWarning("Select Profile Frame position on screen")
        view = FreeCADGui.ActiveDocument.ActiveView
        self.tracker = ViewTracker(view, "Mouse", key="Left", function=self.set_placement)
        self.tracker.start()

    def set_placement(self, callback):
        profile_frame = make_profile_frame.create()
        
        alignment = self.alignment_selector.selected_object
        for item in alignment.Group:
            if item.Proxy.Type == "Road::Profiles":
                item.addObject(profile_frame)
                break

        event = callback.getEvent()
        position = event.getPosition() #Window position
        view = FreeCADGui.ActiveDocument.ActiveView
        coordinate = view.getPoint(tuple(position.getValue()))
        coordinate.z = 0

        profile_frame.Placement.Base = coordinate
        profile_frame.Terrains = self.terrain_selector.selected_objects

        self.tracker.stop()

        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.Control.closeDialog()


class ProfileCreateEdit:
    """Command to create and edit selected Profile."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "ProfileCreateEdit.svg"),
            "MenuText": "Create/Edit Profile",
            "ToolTip": "Create or edit profiles for selected Profile Frame."
            }

    def IsActive(self):
        for obj in FreeCADGui.Selection.getSelection():
            if obj.Proxy.Type == "Road::ProfileFrame":
                self.profile_frame = obj
                return True
        return False

    def Activated(self):
        profiles = self.profile_frame.getParentGroup()
        alignment = profiles.getParentGroup()
        self.form = ProfileEditor(alignment)
        FreeCADGui.Control.showDialog(self)

    def needsFullSpace(self):
        return True
    

class ProfileAdd:
    """Command to add Terrain Profile."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "ProfileAdd.svg"),
            "MenuText": "Add Terrain Profile",
            "ToolTip": "Add Terrain Profile to the selected Profile Frame."
            }

    def IsActive(self):
        for obj in FreeCADGui.Selection.getSelection():
            if obj.Proxy.Type == "Road::ProfileFrame":
                self.profile_frame = obj
                return True
        return False

    def Activated(self):
        terrains = FreeCAD.ActiveDocument.getObject("Terrains")
        self.terrain_selector = MultipleSelection(terrains)

        self.form = self.terrain_selector
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        self.terrains = self.terrain_selector.selected_objects
        self.profile_frame.Terrains = self.terrains

        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("Profile Frame Create", ProfileFrameCreate())
FreeCADGui.addCommand("Profile Create/Edit", ProfileCreateEdit())
FreeCADGui.addCommand("Profile Add", ProfileAdd())
