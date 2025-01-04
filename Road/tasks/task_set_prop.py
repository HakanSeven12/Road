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

"""Provides the general task panel code to select target object type."""

import FreeCAD, FreeCADGui

from ..variables import ui_path
from .task_panel import TaskPanel


class TaskSetProperty(TaskPanel):

    def __init__(self, obj, prop, group):
        self.form = FreeCADGui.PySideUic.loadUi(ui_path + '/selector.ui')
        self.form.setWindowTitle('Select from ' + group.Label)
        self.form.setWindowIcon(group.ViewObject.Icon)
        self.prev = getattr(obj, prop)
        self.object = obj
        self.property = prop
        self.list_targets(self.prev, group)

    def list_targets(self, prev, group):
        self.group_dict = {}
        for i in group.Group:
            if i in prev: continue
            self.group_dict[i.Label] = i

        keys = list(self.group_dict.keys())
        self.form.lw_objects.addItems(keys)

    def accept(self):
        items = self.form.lw_objects.selectedItems()

        selected = []
        for i in items:
            selected.append(self.group_dict[i.text()])

        setattr(self.object, self.property, self.prev + selected)

        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()
