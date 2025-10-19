# SPDX-License-Identifier: LGPL-2.1-or-later

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
