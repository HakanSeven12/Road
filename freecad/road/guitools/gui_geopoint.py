# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to GeoPoint commands."""

import FreeCAD, FreeCADGui
import os
from .. import ICONPATH
from ..make import make_geopoints
from ..tasks.task_selection import SingleSelection
from ..utils.trackers import ViewTracker


class GeoPointsAdd:
    """Command to create a new GeoPoint."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "GeoPointCreate.svg"),
            "MenuText": "Create GeoPoint",
            "ToolTip": "Create GeoPoint by coordinates."
            }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        clusters = FreeCAD.ActiveDocument.getObject("Clusters")
        self.cluster_selector = SingleSelection(clusters)

        self.form = self.cluster_selector
        FreeCADGui.Control.showDialog(self)

    def accept(self):
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
        coord = view.getPoint(tuple(position.getValue()))
        origin = FreeCAD.ActiveDocument.getObject("GeoOrigin")
        coordinate = coord.add(origin.Base)

        model = self.cluster.Model.copy()
        key = self.get_key(model)
        print("test")
        model[key] = {
                "Name": 'GeoPoint', 
                "Easting": coordinate.x/1000, 
                "Northing": coordinate.y/1000, 
                "Elevation": coordinate.z/1000, 
                "Description": ''}
        print("test2")
        self.cluster.Model = model
        FreeCAD.ActiveDocument.recompute()

    def get_key(self, model):
        """Get the next available key as a string, finding the first missing number."""
        if not model:
            return "1"
        
        # Extract all numeric values from string keys
        used = set()
        for key in model.keys():
            try:
                # Try to convert string key to integer
                used.add(int(key))
            except (ValueError, TypeError):
                # Skip keys that aren't numeric strings
                pass
        
        if not used:
            return "1"
        
        # Find the first missing number
        max_key = max(used)
        all_numbers = set(range(1, max_key + 1))
        missing = sorted(all_numbers - used)
        
        if missing:
            # Return first missing number as string
            return str(missing[0])
        else:
            # No gaps, return next number as string
            return str(max_key + 1)


class GeoPointsCreate:
    """Command to create a new GeoPoint Cluster"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "ClusterCreate.svg"),
            "MenuText": "Create Cluster",
            "ToolTip": "Create an empty GeoPoint Cluster."
            }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        make_geopoints.create()
        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("GeoPoints Create", GeoPointsCreate())
FreeCADGui.addCommand("GeoPoints Add", GeoPointsAdd())