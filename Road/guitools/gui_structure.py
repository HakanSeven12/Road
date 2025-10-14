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
        structures = FreeCAD.ActiveDocument.getObject("Structures")
        self.structure = make_structure.create()
        structures.addObject(self.structure)

        FreeCAD.Console.PrintWarning("Select Structure position on screen")
        view = FreeCADGui.ActiveDocument.ActiveView
        self.tracker = ViewTracker(view, "Mouse", key="Left", function=self.set_placement)
        self.tracker.start()

    def set_placement(self, callback):
        event = callback.getEvent()
        position = event.getPosition() #Window position
        view = FreeCADGui.ActiveDocument.ActiveView
        coordinate = view.getPoint(tuple(position.getValue()))
        coordinate.z = 0

        origin = FreeCAD.ActiveDocument.getObject("GeoOrigin")
        if origin:
            coordinate = coordinate.add(origin.Base)

        self.structure.Placement.Base = coordinate
        self.tracker.stop()

        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("Structure Create", StructureCreate())
