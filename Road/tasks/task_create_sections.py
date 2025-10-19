# SPDX-License-Identifier: LGPL-2.1-or-later

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
