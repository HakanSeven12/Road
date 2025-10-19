# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to import LandXML."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..tasks import task_landxml_import


class LandXMLImport:
    """Command to import LandXML file which includes terrain and alignment data."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary."""

        return {
            "Pixmap": icons_path + "/LandXMLImport.svg",
            "MenuText": "Import LandXML",
            "ToolTip": "Import terrain and alignment from LandXML file."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        panel = task_landxml_import.TaskLandXMLImport()
        FreeCADGui.Control.showDialog(panel)
        
        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("LandXML Import", LandXMLImport())
