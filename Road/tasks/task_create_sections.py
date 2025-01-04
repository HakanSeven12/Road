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

"""Provides the task panel code for the Create Sections tool."""

import FreeCAD, FreeCADGui
from pivy import coin

from ..variables import ui_path
from .task_panel import TaskPanel
from ..utils import get_group
from ..make import make_section


class TaskCreateSections(TaskPanel):
    def __init__(self):
        # Set UI.
        self.form = FreeCADGui.PySideUic.loadUi(ui_path + "/create_sections.ui")

        # Add point groups to QListWidget
        self.terrain_list = {}
        terrains = get_group.get("Terrains")
        for terrain in terrains.Group:
            self.terrain_list[terrain.Label] = terrain
            self.form.SelectSurfacesLW.addItem(terrain.Label)

    def accept(self):
        """
        Start event to detect mouse click
        """
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.callback = self.view.addEventCallbackPivy(
            coin.SoButtonEvent.getClassTypeId(), self.select_position)

    def select_position(self, event):
        """
        Select section views location
        """
        # Get event
        event = event.getEvent()

        # If mouse left button pressed get picked point
        if event.getTypeId().isDerivedFrom(coin.SoMouseButtonEvent.getClassTypeId()):
            if event.getButton() == coin.SoMouseButtonEvent.BUTTON1 \
                and event.getState() == coin.SoMouseButtonEvent.DOWN:

                # Finish event
                self.view.removeEventCallbackPivy(
                    coin.SoButtonEvent.getClassTypeId(), self.callback)

                pos = event.getPosition().getValue()
                position = self.view.getPoint(pos[0], pos[1])
                position.z = 0

                region = FreeCADGui.Selection.getSelection()[-1]

                for item in region.Group:
                    if item.Proxy.Type == 'Trails::Sections':
                        cs = item
                        cs.Position = position
                        break

                for item in self.form.SelectSurfacesLW.selectedItems():
                    surface = self.terrain_list[item.text()]
                    sec = make_section.create()
                    cs.addObject(sec)
                    sec.Surface = surface

                FreeCAD.ActiveDocument.recompute()
                FreeCADGui.Control.closeDialog()
