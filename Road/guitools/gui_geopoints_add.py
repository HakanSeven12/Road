# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create GeoPoint objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_geopoints
from ..tasks.task_selection import SingleSelection
from ..utils.trackers import ViewTracker


class GeoPointsAdd:
    """Command to create a new GeoPoint."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary."""
        return {
            "Pixmap": icons_path + "/GeoPointCreate.svg",
            "MenuText": "Create GeoPoint",
            "ToolTip": "Create GeoPoint by coordinates."
            }

    def IsActive(self):
        """Define tool button activation situation."""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        clusters = FreeCAD.ActiveDocument.getObject("Clusters")
        self.cluster_selector = SingleSelection(clusters)

        self.form = self.cluster_selector
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        """Panel 'OK' button clicked"""
        self.cluster = self.cluster_selector.selected_object
        FreeCADGui.Control.closeDialog()

        FreeCAD.Console.PrintWarning("Select GeoPoint location on screen")
        view = FreeCADGui.ActiveDocument.ActiveView
        tracker = ViewTracker(view, "Mouse", key="Left", function=self.set_placement)
        tracker.start()

    def set_placement(self, callback):
        event = callback.getEvent()
        position = event.getPosition() #Window position
        view = FreeCADGui.ActiveDocument.ActiveView
        coordinate = view.getPoint(tuple(position.getValue()))
        coordinate.z = 0

        origin = FreeCAD.ActiveDocument.getObject("GeoOrigin")
        if origin:
            coordinate = coordinate.add(origin.Base)

        geopoint = make_geopoints.create()
        geopoint.Placement.move(coordinate)
        self.cluster.addObject(geopoint)
        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("GeoPoints Add", GeoPointsAdd())
