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

"""Provides GUI tools to create an Offset Alignment objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_alignment
from ..tasks.task_selection import SingleSelection


class AlignmentOffset:
    """Command to create an offset Alignment."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/AlignmentOffset.svg",
            "MenuText": "Create Offset Alignment",
            "ToolTip": "Create an Offset Alignment from another Alignment at a distance."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        self.parent_selector = SingleSelection(alignments)
        
        self.form = self.parent_selector
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        parent_label = self.parent_selector.combo_box.currentText()
        parent = self.parent_selector.objects[parent_label]

        alignment = make_alignment.create()
        alignment.OffsetLength = 5000
        alignment.OffsetAlignment = parent
        alignment.ViewObject.DisplayMode = "Offset"

        FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand("Alignment Offset", AlignmentOffset())
