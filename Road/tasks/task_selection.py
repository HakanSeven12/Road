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

"""Provides the general task panel code to select parent object."""

import FreeCAD, FreeCADGui

from PySide.QtCore import QObject, Signal

from variables import ui_path


class TaskSelectObjectFromGroup(QObject):
    accepted = Signal(list)

    def __init__(self,groups):
        super().__init__()
        self.form = []

        for group in groups:
            obj = FreeCAD.ActiveDocument.getObject(group)
            panel = FreeCADGui.PySideUic.loadUi(ui_path + '/selector.ui')
            self.list_objects(panel, obj)
            self.form.append(panel)

    def list_objects(self, panel, obj):
        panel.setWindowTitle('Select from ' + obj.Label)
        panel.setWindowIcon(obj.ViewObject.Icon)
        panel.group_dict = {}
        for i in obj.Group:
            panel.group_dict[i.Label] = i

        keys = list(panel.group_dict.keys())
        panel.lw_objects.addItems(keys)

    def accept(self):
        selected_objects = []
        for panel in self.form:
            selection = panel.lw_objects.selectedItems()
            if selection: selected_objects.append(
                    [panel.group_dict[sel.text()] for sel in selection])
            else: selected_objects.append([])

        self.accepted.emit(selected_objects)
        FreeCADGui.Control.closeDialog()
