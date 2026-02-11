# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create a Structure objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_structure
from ..utils.trackers import ViewTracker


class StructureCreate:
    """Command to create a Structure."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/StructureCreate.svg",
            "MenuText": "Create Structure",
            "ToolTip": "Create a road Structure."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""

        FreeCAD.Console.PrintWarning("Select Structure position on screen")
        view = FreeCADGui.ActiveDocument.ActiveView
        self.tracker = ViewTracker(view, "Mouse", key="Left", function=self.set_placement)
        self.tracker.start()

    def set_placement(self, callback):
        structure = make_structure.create()

        event = callback.getEvent()
        position = event.getPosition() #Window position
        view = FreeCADGui.ActiveDocument.ActiveView
        coordinate = view.getPoint(tuple(position.getValue()))
        coordinate.z = 0

        structure.Placement.Base = coordinate
        self.tracker.stop()

        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("Structure Create", StructureCreate())
