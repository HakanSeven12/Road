# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Section objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_section_frame_group, make_section
from ..tasks.task_selection import SingleSelection, MultipleSelection
from ..utils.trackers import ViewTracker


class CreateSections:

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
        region = self.region_selector.selected_object
        print(region.Label)
        self.terrains = self.terrain_selector.selected_objects
        self.section_frame_group = make_section_frame_group.create()

        for item in region.Group:
            print(item.Proxy.Type )
            if item.Proxy.Type == "Road::Sections":
                item.addObject(self.section_frame_group)
                break

        FreeCAD.Console.PrintWarning("Select Section Frame Group position on screen")
        view = FreeCADGui.ActiveDocument.ActiveView
        self.tracker = ViewTracker(view, "Mouse", key="Left", function=self.set_placement)
        self.tracker.start()

        FreeCADGui.Control.closeDialog()

    def set_placement(self, callback):
        print(callback)
        event = callback.getEvent()
        position = event.getPosition() #Window position
        view = FreeCADGui.ActiveDocument.ActiveView
        coordinate = view.getPoint(tuple(position.getValue()))
        coordinate.z = 0

        origin = FreeCAD.ActiveDocument.getObject("GeoOrigin")
        if origin:
            coordinate = coordinate.add(origin.Base)

        self.section_frame_group.Placement.Base = coordinate
        print("test")
        self.tracker.stop()

        for i in self.terrains:
            section = make_section.create()
            self.section_frame_group.addObject(section)
            section.ViewObject.DisplayMode = "Terrain"
            section.Terrain = i

        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Section Frame Group Create", CreateSections())
