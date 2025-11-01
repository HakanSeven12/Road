# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to export GeoPoints."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..tasks import task_geopoints_export


class GeoPointsExport:
    """Command to export points to point file."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary."""

        return {
            "Pixmap": icons_path + "/ExportPoints.svg",
            "MenuText": "Export GeoPoints",
            "ToolTip": "Export GeoPoints to file."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        panel = task_geopoints_export.TaskGeoPointsExport()
        FreeCADGui.Control.showDialog(panel)

        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("GeoPoints Export", GeoPointsExport())
