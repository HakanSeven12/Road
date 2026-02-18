# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to Alignment commands."""

import FreeCAD, FreeCADGui
import os
from .. import ICONPATH
from ..make import make_alignment
from ..tasks import task_alignment_editor 
from ..tasks.task_alignment_object import TaskAlignmentObject
from ..tasks.task_selection import SingleSelection


class AlignmentCreate:
    """Command to create a new Alignment."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "AlignmentCreate.svg"),
            "MenuText": "Create Alignment",
            "ToolTip": "Create Alignment geometry."}

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        # Check for selected object
        alignment = make_alignment.create()

        panel = task_alignment_editor.run(alignment)
        FreeCADGui.Control.showDialog(panel)

        FreeCAD.ActiveDocument.recompute()


class AlignmentEdit:
    """Command to edit selected Alignment geometry."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "AlignmentEdit.svg"),
            "MenuText": "Edit Alignment",
            "ToolTip": "Edit selected Alignment geometry."
            }

    def IsActive(self):
        for obj in FreeCADGui.Selection.getSelection():
            if obj.Proxy.Type == "Road::Alignment":
                self.alignment = obj
                return True
        return False

    def Activated(self):
        panel = task_alignment_editor.run(self.alignment)
        FreeCADGui.Control.showDialog(panel)

        FreeCAD.ActiveDocument.recompute()
        

class AlignmentObject:
    """Command to create an Alignment from a 2D object (Draft, Sketch, etc.)"""
    
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "AlignmentObject.svg"),
            "MenuText": "Create Alignment From Object",
            "ToolTip": "Create an Alignment from 2D object (Draft or Sketch)."
        }
    
    def IsActive(self):
        # Active if document exists and selection contains valid geometry
        if not FreeCADGui.ActiveDocument:
            return False
        
        selection = FreeCADGui.Selection.getSelection()
        if len(selection) != 1:
            return False
        
        obj = selection[0]
        return self._is_valid_object(obj)
    
    def _is_valid_object(self, obj):
        """Check if object has valid 2D geometry for alignment creation"""
        if not hasattr(obj, 'Shape'):
            return False
        
        shape = obj.Shape
        if shape.isNull():
            return False
        
        # Check if shape has edges (wires, lines, arcs, etc.)
        if len(shape.Edges) == 0:
            return False
        
        return True
    
    def Activated(self):
        selection = FreeCADGui.Selection.getSelection()
        
        if len(selection) != 1:
            FreeCAD.Console.PrintError("Please select exactly one 2D object.\n")
            return
        
        obj = selection[0]
        
        if not self._is_valid_object(obj):
            FreeCAD.Console.PrintError("Selected object has no valid geometry.\n")
            return
        
        # Create and show task panel
        panel = TaskAlignmentObject(obj)
        FreeCADGui.Control.showDialog(panel)


class AlignmentOffset:
    """Command to create an offset Alignment."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "AlignmentOffset.svg"),
            "MenuText": "Create Offset Alignment",
            "ToolTip": "Create an Offset Alignment from another Alignment at a distance."
            }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        self.parent_selector = SingleSelection(alignments)
        
        self.form = self.parent_selector
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        parent = self.parent_selector.selected_object

        alignment = make_alignment.create()
        alignment.Parent = parent
        alignment.OffsetLength = 5
        alignment.Model.coordinate_system.set_system('custom', alignment.Model.start_point, swap=True)
        #alignment.ViewObject.DisplayMode = "Offset"

        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("Alignment Create", AlignmentCreate())
FreeCADGui.addCommand("Alignment Edit", AlignmentEdit())
FreeCADGui.addCommand("Alignment Object", AlignmentObject())
FreeCADGui.addCommand("Alignment Offset", AlignmentOffset())
