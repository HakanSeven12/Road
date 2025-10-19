# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Component Line objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_component_line


class ComponentLine:
    """Command to create a new Component Line."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/ComponentLine.svg",
            "MenuText": "Add Component Line",
            "ToolTip": "Add Line geometry to the selected Component."
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
        line = make_component_line.create()
        self.component.addObject(line)

        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Component Line", ComponentLine())
