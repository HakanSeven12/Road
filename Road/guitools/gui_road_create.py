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

"""Provides GUI tools to create a Road objects."""

import FreeCAD, FreeCADGui

from ..variables import icons_path
#from ..make import make_road
from ..tasks.task_selection import SingleSelection


class RoadCreate:
    """Command to create a Road."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            'Pixmap': icons_path + '/RoadCreate.svg',
            'MenuText': "Create Road",
            'ToolTip': "Create a Road from alignment, profile and structure."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        self.alignment_selector = SingleSelection(alignments)
        self.alignment_selector.combo_box.currentTextChanged.connect(self.frame_update)

        self.frame_selector = SingleSelection()
        self.frame_selector.combo_box.currentTextChanged.connect(self.profile_update)
        self.frame_update()

        self.profile_selector = SingleSelection()
        self.profile_update()

        structures = FreeCAD.ActiveDocument.getObject("Structures")
        self.structure_selector = SingleSelection(structures)

        self.form = [self.alignment_selector, self.frame_selector, self.profile_selector, self.structure_selector]
        FreeCADGui.Control.showDialog(self)

    def frame_update(self):
        alignment_label = self.alignment_selector.combo_box.currentText()
        alignment = self.alignment_selector.objects[alignment_label]

        for item in alignment.Group:
            if item.Proxy.Type == 'Road::Profiles':
                self.frame_selector.update_items(item)

    def profile_update(self):
        frame_label = self.frame_selector.combo_box.currentText()
        profile_frame = self.frame_selector.objects[frame_label]
        self.profile_selector.update_items(profile_frame)

    def accept(self):
        """Panel 'OK' button clicked"""
        alignment_label = self.alignment_selector.combo_box.currentText()
        alignment = self.alignment_selector.objects[alignment_label]

        profile_label = self.profile_selector.combo_box.currentText()
        profile = self.profile_selector.objects[profile_label]

        structure_label = self.structure_selector.combo_box.currentText()
        structure = self.structure_selector.objects[structure_label]

        #self.profile_frame = make_profile_frame.create()

        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand('Road Create', RoadCreate())
