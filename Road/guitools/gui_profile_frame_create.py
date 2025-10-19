# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create a Profile Frame objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_profile_frame, make_profile
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
        alignment = self.alignment_selector.selected_object
        self.terrains = self.terrain_selector.selected_objects
        self.profile_frame = make_profile_frame.create()

        for item in alignment.Group:
            if item.Proxy.Type == "Road::Profiles":
                item.addObject(self.profile_frame)
                break

        FreeCAD.Console.PrintWarning("Select Profile Frame position on screen")
        view = FreeCADGui.ActiveDocument.ActiveView
        self.tracker = ViewTracker(view, "Mouse", key="Left", function=self.set_placement)
        self.tracker.start()

        FreeCADGui.Control.closeDialog()

    def set_placement(self, callback):
        event = callback.getEvent()
        position = event.getPosition() #Window position
        view = FreeCADGui.ActiveDocument.ActiveView
        coordinate = view.getPoint(tuple(position.getValue()))
        coordinate.z = 0

        origin = FreeCAD.ActiveDocument.getObject("GeoOrigin")
        if origin:
            coordinate = coordinate.add(origin.Base)

        self.profile_frame.Placement.Base = coordinate
        self.tracker.stop()

        for i in self.terrains:
            profile = make_profile.create()
            self.profile_frame.addObject(profile)
            profile.ViewObject.DisplayMode = "Terrain"
            profile.Terrain = i

        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("Profile Frame Create", ProfileFrameCreate())
