# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Component objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_component


class ComponentAdd:
    """Command to create a new Component."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/ComponentAdd.svg",
            "MenuText": "Add Component",
            "ToolTip": "Add Component to the selected Structure."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        for obj in FreeCADGui.Selection.getSelection():
            if obj.Proxy.Type == "Road::Structure":
                self.structure = obj
                return True
        return False

    def Activated(self):
        """Command activation method"""
        component = make_component.create()
        self.structure.addObject(component)

        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Component Add", ComponentAdd())
