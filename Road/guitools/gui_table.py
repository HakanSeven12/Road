# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Table objects."""

import FreeCAD, FreeCADGui
from pivy import coin

from ..variables import icons_path
from ..make import make_table


class CreateTable:

    def __init__(self):
        """
        Constructor
        """
        pass

    def GetResources(self):
        """
        Return the command resources dictionary
        """
        return {
            'Pixmap': icons_path + '/table.svg',
            'MenuText': "Create Volume Table",
            'ToolTip': "Create Volume Table"
            }

    def IsActive(self):
        """
        Define tool button activation situation
        """
        # Check for document
        if FreeCAD.ActiveDocument:
            # Check for selected object
            self.selection = FreeCADGui.Selection.getSelection()
            if self.selection:
                if self.selection[-1].Proxy.Type == 'Road::Volume':
                    return True
        return False

    def Activated(self):
        """
        Command activation method
        """
        #Start event to detect mouse click
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

                vol_group = self.selection[-1].getParentGroup()
                region = vol_group.getParentGroup()

                for item in region.Group:
                    if item.Proxy.Type == 'Trails::Tables':
                        tables = item
                        break

                tab = make_table.create(tables, position, self.selection[-1])

                FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand('Create Table', CreateTable())
