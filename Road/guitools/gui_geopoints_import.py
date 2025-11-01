# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to import GeoPoints."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..tasks import task_geopoints_import


class GeoPointsImport:
    """Command to import point file which includes survey data."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary."""

        return {
            "Pixmap": icons_path + "/ImportPointFile.svg",
            "MenuText": "Import GeoPoints",
            "ToolTip": "Import GeoPoints from file."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        panel = task_geopoints_import.TaskGeoPointsImport()
        FreeCADGui.Control.showDialog(panel)
        
        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("GeoPoints Import", GeoPointsImport())
