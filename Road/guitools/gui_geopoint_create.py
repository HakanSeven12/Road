# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2025 Hakan Seven <hakanseven12@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""Provides GUI tools to create GeoPoint objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_geopoint,make_cluster
from ..tasks.task_selection import SingleSelection
from ..utils.trackers import ViewTracker
from ..utils import get_group


class GeoPointCreate:
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
        cluster_label = self.cluster_selector.combo_box.currentText()
        self.cluster = self.cluster_selector.objects[cluster_label]

        FreeCADGui.Control.closeDialog()

        FreeCAD.Console.PrintWarning("Select GeoPoint location on screen")
        tracker = ViewTracker("Mouse", key="Left", function=self.set_placement)
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

        geopoint = make_geopoint.create()
        geopoint.Placement.move(coordinate)
        self.cluster.addObject(geopoint)
        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("GeoPoint Create", GeoPointCreate())
