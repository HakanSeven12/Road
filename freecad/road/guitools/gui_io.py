# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to Input/Output commands."""

import FreeCAD, FreeCADGui
import os
from .. import ICONPATH
from ..tasks import (task_geopoints_import,
                     task_geopoints_export,
                     task_landxml_import)


class GeoPointsImport:
    """Command to import point file which includes survey data."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "ImportPointFile.svg"),
            "MenuText": "Import GeoPoints",
            "ToolTip": "Import GeoPoints from file."
            }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        panel = task_geopoints_import.TaskGeoPointsImport()
        FreeCADGui.Control.showDialog(panel)
        
        FreeCAD.ActiveDocument.recompute()


class GeoPointsExport:
    """Command to export points to point file."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "ExportPoints.svg"),
            "MenuText": "Export GeoPoints",
            "ToolTip": "Export GeoPoints to file."
            }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        panel = task_geopoints_export.TaskGeoPointsExport()
        FreeCADGui.Control.showDialog(panel)

        FreeCAD.ActiveDocument.recompute()


class LandXMLImport:
    """Command to import LandXML file."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "LandXMLImport.svg"),
            "MenuText": "Import LandXML",
            "ToolTip": "Import objects from LandXML file."
            }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        panel = task_landxml_import.TaskLandXMLImport()
        FreeCADGui.Control.showDialog(panel)
        
        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("GeoPoints Import", GeoPointsImport())
FreeCADGui.addCommand("GeoPoints Export", GeoPointsExport())
FreeCADGui.addCommand("LandXML Import", LandXMLImport())