# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2025 Hakan Seven <hakanseven12@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

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
