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

"""Provides GUI tools to create Alignment objects."""

import FreeCAD, FreeCADGui

from variables import icons_path
from ..tasks import task_alignment_editor


class EditAlignment:
    """
    Command to create a new Alignment.
    """

    def __init__(self):
        """
        Constructor
        """
        pass

    def GetResources(self):
        """
        Return the command resources dictionary
        """
        return {
            'Pixmap': icons_path + '/AlignmentEdit.svg',
            'MenuText': "Edit Alignment",
            'ToolTip': "Edit selected Alignment."
            }

    def IsActive(self):
        """
        Define tool button activation situation
        """
        # Check for document
        if FreeCAD.ActiveDocument:
            # Check for selected object
            selection = FreeCADGui.Selection.getSelection()
            if selection:
                if selection[-1].Proxy.Type == 'Road::Alignment':
                    return True
        return False

    def Activated(self):
        """
        Command activation method
        """
        # Check for selected object
        selection = FreeCADGui.Selection.getSelection()

        if selection:
            alignment = selection[0] 

            panel = task_alignment_editor.run(alignment=alignment)
            FreeCADGui.Control.showDialog(panel)

            FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand('Edit Alignment', EditAlignment())
