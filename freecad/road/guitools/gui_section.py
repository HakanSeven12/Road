# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to Section commands."""

import FreeCAD, FreeCADGui
import os
from .. import ICONPATH
from ..make import make_section, make_region, make_table
from ..tasks.task_selection import SingleSelection, MultipleSelection
from ..utils.trackers import ViewTracker
from pivy import coin


class RegionCreate:
    """Command to create a new Region object for selected alignment"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "RegionCreate.svg"),
            "MenuText": "Create Region",
            "ToolTip": "Create Region lines at stations along an alignment"
            }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        self.alignment_selector = SingleSelection(alignments)

        self.form = self.alignment_selector
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        alignment = self.alignment_selector.selected_object
        make_region.create(alignment)
        
        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()


class SectionCreate:

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "CreateSections.svg"),
            'MenuText': "Create Section Views",
            'ToolTip': "Create Section Views"
            }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        self.alignment_selector = SingleSelection(alignments)
        self.alignment_selector.combo_box.currentTextChanged.connect(self.region_update)

        self.region_selector = SingleSelection()
        self.region_update()

        terrains = FreeCAD.ActiveDocument.getObject("Terrains")
        self.terrain_selector = MultipleSelection(terrains)

        self.form = [self.alignment_selector, self.region_selector, self.terrain_selector]
        FreeCADGui.Control.showDialog(self)

    def region_update(self):
        alignment = self.alignment_selector.selected_object
        for item in alignment.Group:
            if item.Proxy.Type == "Road::Regions":
                self.region_selector.set_group(item)
                break

    def accept(self):
        FreeCAD.Console.PrintWarning("Select Section Frame Group position on screen")
        view = FreeCADGui.ActiveDocument.ActiveView
        self.tracker = ViewTracker(view, "Mouse", key="Left", function=self.set_placement)
        self.tracker.start()

    def set_placement(self, callback):
        section = make_section.create()

        region = self.region_selector.selected_object
        for item in region.Group:
            if item.Proxy.Type == "Road::Sections":
                item.addObject(section)
                break

        event = callback.getEvent()
        position = event.getPosition() #Window position
        view = FreeCADGui.ActiveDocument.ActiveView
        coordinate = view.getPoint(tuple(position.getValue()))
        coordinate.z = 0

        section.Placement.Base = coordinate
        section.Terrains = self.terrain_selector.selected_objects

        self.tracker.stop()

        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.Control.closeDialog()
        

class ComputeAreas:
    """Command to compute areas between surface sections"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "volume.svg"),
            'MenuText': "Compute areas",
            'ToolTip': "Compute areas between surface sections"
            }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        # Check for selected object
        region = FreeCADGui.Selection.getSelection()
        #panel = task_create_volume.TaskCreateVolume()
        #FreeCADGui.Control.showDialog(panel)
        
        FreeCAD.ActiveDocument.recompute()
        

class CreateTable:

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "table.svg"),
            'MenuText': "Create Volume Table",
            'ToolTip': "Create Volume Table"
            }

    def IsActive(self):
        # Check for document
        if FreeCAD.ActiveDocument:
            # Check for selected object
            self.selection = FreeCADGui.Selection.getSelection()
            if self.selection:
                if self.selection[-1].Proxy.Type == 'Road::Volume':
                    return True
        return False

    def Activated(self):
        #Start event to detect mouse click
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.callback = self.view.addEventCallbackPivy(
            coin.SoButtonEvent.getClassTypeId(), self.select_position)

    def select_position(self, event):
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


FreeCADGui.addCommand("Region Create", RegionCreate())
FreeCADGui.addCommand("Section Create", SectionCreate())
FreeCADGui.addCommand('Compute Areas', ComputeAreas())
FreeCADGui.addCommand('Create Table', CreateTable())
