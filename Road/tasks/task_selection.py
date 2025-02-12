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

"""Provides the general task panel code to select objects from a group."""

from PySide.QtWidgets import QWidget, QVBoxLayout, QComboBox, QListWidget, QListWidgetItem, QAbstractItemView
from PySide.QtCore import Qt

class SingleSelection(QWidget):
    def __init__(self, group=None):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.combo_box = QComboBox()
        layout.addWidget(self.combo_box)

        if group: self.update_items(group)

    def update_items(self,group):
        """Update the combo box items dynamically."""
        self.setWindowTitle("Select from " + group.Label)
        self.setWindowIcon(group.ViewObject.Icon)

        self.objects = {i.Label: i for i in group.Group}
        keys = list(self.objects.keys())

        self.combo_box.clear()
        self.combo_box.addItems(keys)

class MultipleSelection(QWidget):
    def __init__(self, group):
        super().__init__()
        self.setWindowTitle("Select from " + group.Label)
        self.setWindowIcon(group.ViewObject.Icon)

        self.objects = {i.Label: i for i in group.Group}
        keys = list(self.objects.keys())

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        for i in keys:
            item = QListWidgetItem(i)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)

        self.list_widget.itemSelectionChanged.connect(self.sync_selection_with_check)

    def sync_selection_with_check(self):
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            if item in self.list_widget.selectedItems():
                if item.checkState() != Qt.Checked:
                    item.setCheckState(Qt.Checked)
            else:
                if item.checkState() != Qt.Unchecked:
                    item.setCheckState(Qt.Unchecked)