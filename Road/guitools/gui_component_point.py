# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Component Point objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_component_point


class ComponentPoint:
    """Command to create a new Component Point."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/ComponentPoint.svg",
            "MenuText": "Add Component Point",
            "ToolTip": "Add Point geometry to the selected Component."
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
        point = make_component_point.create()
        self.component.addObject(point)

        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Component Point", ComponentPoint())
