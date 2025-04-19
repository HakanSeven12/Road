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

"""Provides GUI tools to create Region objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
from ..make import make_region
from ..tasks.task_selection import SingleSelection


class RegionCreate:
    """Command to create a new Region object for selected alignment"""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/RegionCreate.svg",
            "MenuText": "Create Region",
            "ToolTip": "Create Region lines at stations along an alignment"
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        self.alignment_selector = SingleSelection(alignments)

        self.form = self.alignment_selector
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        """Panel 'OK' button clicked"""
        alignment_label = self.alignment_selector.combo_box.currentText()
        alignment = self.alignment_selector.objects[alignment_label]

        FreeCADGui.Control.closeDialog()
        make_region.create(alignment)
        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("Region Create", RegionCreate())
