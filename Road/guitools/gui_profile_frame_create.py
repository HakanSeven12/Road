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

"""Provides GUI tools to create a Profile Frame objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_profile_frame, make_profile
from ..tasks.task_selection import TaskSelectObjectFromGroup
from ..utils.trackers import ViewTracker


class ProfileFrameCreate:
    """Command to create a Profile Frame."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            'Pixmap': icons_path + '/ProfileFrameCreate.svg',
            'MenuText': "Create Profile Frame",
            'ToolTip': "Create a Profile Frame for selected Alignment."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        tracker = ViewTracker("Location")
        tracker.start()
        selection = FreeCADGui.Selection.getSelection()
        if selection:
            if selection[-1].Proxy.Type == 'Road::Alignment':
                self.create([selection[-1],[]])
                return

        panel = TaskSelectObjectFromGroup(["Alignments", "Terrains"])
        panel.accepted.connect(self.create)

        FreeCADGui.Control.showDialog(panel)

    def create(self, selected_objects):
        alignment = selected_objects[0][0]
        self.terrains = selected_objects[1]
        self.profile_frame = make_profile_frame.create()

        for item in alignment.Group:
            if item.Proxy.Type == 'Road::Profiles':
                item.addObject(self.profile_frame)
                break

        FreeCAD.Console.PrintWarning("Select Profile Frame position on screen")
        self.tracker = ViewTracker("Mouse", key="Left", function=self.set_placement)
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

        self.profile_frame.Placement.Base = coordinate
        self.tracker.stop()

        if self.terrains:
            for i in self.terrains:
                profile = make_profile.create()
                self.profile_frame.addObject(profile)
                profile.Terrain = i

        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand('Profile Frame Create', ProfileFrameCreate())
