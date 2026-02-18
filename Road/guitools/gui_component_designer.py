# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to open Component Designer."""

import FreeCADGui
from ..variables import icons_path
#from ..externals.component_designer import component_designer


class ComponentDesigner:
    """Command to open Component Designer."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/ComponentDesigner.svg",
            "MenuText": "Component Designer",
            "ToolTip": "Node based component designer."}

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        # Check for selected object
        #component_designer.main()
        pass

FreeCADGui.addCommand("Component Designer", ComponentDesigner())
