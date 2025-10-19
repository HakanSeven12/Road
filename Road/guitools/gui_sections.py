# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Section objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_section
from ..tasks.task_selection import SingleSelection, MultipleSelection
from ..utils.trackers import ViewTracker


class SectionCreate:

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            'Pixmap': icons_path + '/CreateSections.svg',
            'MenuText': "Create Section Views",
            'ToolTip': "Create Section Views"
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
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
        """Panel 'OK' button clicked"""
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

        origin = FreeCAD.ActiveDocument.getObject("GeoOrigin")
        if origin:
            coordinate = coordinate.add(origin.Base)

        section.Placement.Base = coordinate
        section.Terrains = self.terrain_selector.selected_objects

        self.tracker.stop()

        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.Control.closeDialog()

FreeCADGui.addCommand("Section Create", SectionCreate())
