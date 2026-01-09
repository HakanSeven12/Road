# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create a Profile Frame objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_profile_frame
from ..tasks.task_selection import SingleSelection, MultipleSelection
from ..utils.trackers import ViewTracker


class ProfileFrameCreate:
    """Command to create a Profile Frame."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/ProfileFrameCreate.svg",
            "MenuText": "Create Profile Frame",
            "ToolTip": "Create a Profile Frame for selected Alignment."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        self.alignment_selector = SingleSelection(alignments)

        terrains = FreeCAD.ActiveDocument.getObject("Terrains")
        self.terrain_selector = MultipleSelection(terrains)

        self.form = [self.alignment_selector, self.terrain_selector]
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        """Panel 'OK' button clicked"""
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

FreeCADGui.addCommand("Profile Frame Create", ProfileFrameCreate())
