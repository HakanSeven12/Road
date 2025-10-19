# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Volume objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..tasks import task_create_volume


class ComputeAreas:
    """
    Command to compute areas between surface sections
    """

    def __init__(self):
        """
        Command to create guide lines for selected alignment.
        """
        pass

    def GetResources(self):
        """
        Return the command resources dictionary
        """
        return {
            'Pixmap': icons_path + '/volume.svg',
            'MenuText': "Compute areas",
            'ToolTip': "Compute areas between surface sections"
            }

    def IsActive(self):
        """
        Define tool button activation situation
        """
        # Check for document
        if FreeCAD.ActiveDocument:
            return True
        return False

    def Activated(self):
        """
        Command activation method
        """
        # Check for selected object
        region = FreeCADGui.Selection.getSelection()
        panel = task_create_volume.TaskCreateVolume()
        FreeCADGui.Control.showDialog(panel)
        
        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand('Compute Areas', ComputeAreas())
