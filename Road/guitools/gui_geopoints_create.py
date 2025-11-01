# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Cluster objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from Road.make import make_geopoints


class GeoPointsCreate:
    """Command to create a new GeoPoint Cluster"""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/ClusterCreate.svg",
            "MenuText": "Create Cluster",
            "ToolTip": "Create an empty GeoPoint Cluster."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        make_geopoints.create()
        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("GeoPoints Create", GeoPointsCreate())
