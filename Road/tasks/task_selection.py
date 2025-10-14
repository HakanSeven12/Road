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

"""Task panel widgets for object selection from FreeCAD groups."""

from PySide.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox, 
    QListWidget, QListWidgetItem
)
from PySide.QtCore import Qt


class SingleSelection(QWidget):
    """Combo box widget for selecting a single object from a group."""
    
    def __init__(self, group=None):
        super().__init__()
        self._objects = {}
        self._setup_ui()
        if group:
            self.set_group(group)

    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.combo_box = QComboBox()
        layout.addWidget(self.combo_box)

    def set_group(self, group):
        """
        Populate widget with objects from a FreeCAD group.
        
        Args:
            group: FreeCAD group object containing Group attribute
        """
        if not group or not hasattr(group, 'Group'):
            return
            
        self.setWindowTitle(f"Select from {group.Label}")
        if hasattr(group, 'ViewObject'):
            self.setWindowIcon(group.ViewObject.Icon)

        # Store mapping of label to object
        self._objects = {obj.Label: obj for obj in group.Group}
        
        self.combo_box.clear()
        self.combo_box.addItems(list(self._objects.keys()))

    @property
    def selected_label(self):
        """Get the currently selected item label."""
        return self.combo_box.currentText()
    
    @property
    def selected_object(self):
        """Get the currently selected FreeCAD object."""
        label = self.selected_label
        return self._objects.get(label)
    
    def set_selected(self, label):
        """
        Set the current selection by label.
        
        Args:
            label: Label string of the object to select
        """
        index = self.combo_box.findText(label)
        if index >= 0:
            self.combo_box.setCurrentIndex(index)


class MultipleSelection(QWidget):
    """List widget with checkboxes for selecting multiple objects from a group."""
    
    def __init__(self, group=None):
        super().__init__()
        self._objects = {}
        self._setup_ui()
        if group:
            self.set_group(group)

    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.list_widget)

    def set_group(self, group):
        """
        Populate widget with objects from a FreeCAD group.
        
        Args:
            group: FreeCAD group object containing Group attribute
        """
        if not group or not hasattr(group, 'Group'):
            return
            
        self.setWindowTitle(f"Select from {group.Label}")
        if hasattr(group, 'ViewObject'):
            self.setWindowIcon(group.ViewObject.Icon)

        # Store mapping of label to object
        self._objects = {obj.Label: obj for obj in group.Group}

        self.list_widget.clear()
        for label in self._objects.keys():
            item = QListWidgetItem(label)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)

    @property
    def selected_labels(self):
        """Get list of all checked item labels."""
        return [
            self.list_widget.item(i).text()
            for i in range(self.list_widget.count())
            if self.list_widget.item(i).checkState() == Qt.Checked
        ]
    
    @property
    def selected_objects(self):
        """Get list of all checked FreeCAD objects."""
        return [
            self._objects[label] 
            for label in self.selected_labels
            if label in self._objects
        ]
    
    def select_all(self):
        """Check all items in the list."""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)
    
    def deselect_all(self):
        """Uncheck all items in the list."""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)
    
    def set_selected(self, labels):
        """
        Set checked state for items matching given labels.
        
        Args:
            labels: List of label strings to check
        """
        label_set = set(labels)
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            state = Qt.Checked if item.text() in label_set else Qt.Unchecked
            item.setCheckState(state)