# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Component Shape objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_component_shape


class ComponentShape:
    """Command to create a new Component Shape."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/ComponentShape.svg",
            "MenuText": "Add Component Shape",
            "ToolTip": "Add Shape geometry to the selected Component."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        for obj in FreeCADGui.Selection.getSelection():
            if obj.Proxy.Type == "Road::Component":
                self.component = obj
                return True
        return False

    def Activated(self):
        """Command activation method"""
        shape = make_component_shape.create()
        self.component.addObject(shape)

        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Component Shape", ComponentShape())
