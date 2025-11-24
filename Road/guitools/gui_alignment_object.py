# SPDX-License-Identifier: LGPL-2.1-or-later
"""Provides GUI tools to create an Alignment object from 2D object."""

import FreeCAD, FreeCADGui
from ..variables import icons_path
from ..tasks.task_alignment_object import TaskAlignmentObject


class AlignmentObject:
    """Command to create an Alignment from a 2D object (Draft, Sketch, etc.)"""
    
    def __init__(self):
        """Constructor"""
        pass
    
    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/AlignmentObject.svg",
            "MenuText": "Create Alignment From Object",
            "ToolTip": "Create an Alignment from 2D object (Draft or Sketch)."
        }
    
    def IsActive(self):
        """Define tool button activation situation"""
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
        """Command activation method"""
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

FreeCADGui.addCommand("Alignment Object", AlignmentObject())