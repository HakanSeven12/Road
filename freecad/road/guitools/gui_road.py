# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to Road commands."""

import FreeCAD, FreeCADGui
import os
from .. import ICONPATH
from ..make import (make_road,
                    make_structure,
                    make_component,
                    make_component_point,
                    make_component_line,
                    make_component_shape)
from ..utils.trackers import ViewTracker
from ..tasks.task_selection import SingleSelection, SimpleComboBox
from modules.component_designer.main_window import ComponentDesigner as designer


class RoadCreate:
    """Command to create a Road."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "RoadCreate.svg"),
            "MenuText": "Create Road",
            "ToolTip": "Create a Road from alignment, profile and structure."
            }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        structures = FreeCAD.ActiveDocument.getObject("Structures")

        self.alignment_selector = SingleSelection(alignments)
        self.profile_selector = SimpleComboBox(title="Select Profile")
        self.structure_selector = SingleSelection(structures)

        self.alignment_selector.combo_box.currentTextChanged.connect(self.profile_update)
        self.profile_update()

        self.form = [self.alignment_selector, self.profile_selector, self.structure_selector]
        FreeCADGui.Control.showDialog(self)

    def profile_update(self):
        """Update profile selector when alignment changes"""
        alignment = self.alignment_selector.selected_object
        profiles = alignment.Model.profiles
        profile_names = profiles.get_profalign_names()
        self.profile_selector.update_items(profile_names)

    def accept(self):
        alignment = self.alignment_selector.selected_object
        selected_profile_name = self.profile_selector.selected_item
        structure = self.structure_selector.selected_object

        road = make_road.create()

        road.Alignment = alignment
        road.Profile = selected_profile_name
        road.Structure = structure

        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.Control.closeDialog()


class StructureCreate:
    """Command to create a Structure."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "StructureCreate.svg"),
            "MenuText": "Create Structure",
            "ToolTip": "Create a road Structure."
            }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        FreeCAD.Console.PrintWarning("Select Structure position on screen")
        view = FreeCADGui.ActiveDocument.ActiveView
        self.tracker = ViewTracker(view, "Mouse", key="Left", function=self.set_placement)
        self.tracker.start()

    def set_placement(self, callback):
        structure = make_structure.create()

        event = callback.getEvent()
        position = event.getPosition() #Window position
        view = FreeCADGui.ActiveDocument.ActiveView
        coordinate = view.getPoint(tuple(position.getValue()))
        coordinate.z = 0

        structure.Placement.Base = coordinate
        self.tracker.stop()

        FreeCAD.ActiveDocument.recompute()


class ComponentAdd:
    """Command to create a new Component."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "ComponentAdd.svg"),
            "MenuText": "Add Component",
            "ToolTip": "Add Component to the selected Structure."
            }

    def IsActive(self):
        for obj in FreeCADGui.Selection.getSelection():
            if obj.Proxy.Type == "Road::Structure":
                self.structure = obj
                return True
        return False

    def Activated(self):
        component = make_component.create()
        self.structure.addObject(component)

        FreeCAD.ActiveDocument.recompute()


class ComponentDesigner:
    """Command to open Component Designer."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "ComponentDesigner.svg"),
            "MenuText": "Component Designer",
            "ToolTip": "Node based component designer."}

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        mw = FreeCADGui.getMainWindow()
        window = designer(mw)
        window.show()


class ComponentPoint:
    """Command to create a new Component Point."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "ComponentPoint.svg"),
            "MenuText": "Add Component Point",
            "ToolTip": "Add Point geometry to the selected Component."
            }

    def IsActive(self):
        for obj in FreeCADGui.Selection.getSelection():
            if obj.Proxy.Type == "Road::Component":
                self.component = obj
                return True
        return False

    def Activated(self):
        point = make_component_point.create()
        self.component.addObject(point)

        FreeCAD.ActiveDocument.recompute()


class ComponentLine:
    """Command to create a new Component Line."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "ComponentLine.svg"),
            "MenuText": "Add Component Line",
            "ToolTip": "Add Line geometry to the selected Component."
            }

    def IsActive(self):
        for obj in FreeCADGui.Selection.getSelection():
            if obj.Proxy.Type == "Road::Component":
                self.component = obj
                return True
        return False

    def Activated(self):
        line = make_component_line.create()
        self.component.addObject(line)

        FreeCAD.ActiveDocument.recompute()


class ComponentShape:
    """Command to create a new Component Shape."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "ComponentShape.svg"),
            "MenuText": "Add Component Shape",
            "ToolTip": "Add Shape geometry to the selected Component."
            }

    def IsActive(self):
        for obj in FreeCADGui.Selection.getSelection():
            if obj.Proxy.Type == "Road::Component":
                self.component = obj
                return True
        return False

    def Activated(self):
        shape = make_component_shape.create()
        self.component.addObject(shape)

        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("Road Create", RoadCreate())
FreeCADGui.addCommand("Structure Create", StructureCreate())
FreeCADGui.addCommand("Component Add", ComponentAdd())
FreeCADGui.addCommand("Component Designer", ComponentDesigner())
FreeCADGui.addCommand("Component Point", ComponentPoint())
FreeCADGui.addCommand("Component Line", ComponentLine())
FreeCADGui.addCommand("Component Shape", ComponentShape())
