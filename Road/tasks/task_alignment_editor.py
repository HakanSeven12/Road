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

"""Provides the task panel code for the Alignment Editor tool."""

from PySide.QtWidgets import QVBoxLayout, QPushButton, QTreeView, QWidget, QHBoxLayout, QFileDialog, QComboBox, QStyledItemDelegate
from PySide.QtGui import QStandardItem, QStandardItemModel
from PySide.QtCore import Qt
import csv

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items

    def createEditor(self, parent, option, index):
        combo_box = QComboBox(parent)
        combo_box.addItems(self.items)
        return combo_box

    def setEditorData(self, editor, index):
        value = index.data(Qt.EditRole)
        if value:
            editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

class PiTreeViewWidget(QWidget):
    def __init__(self, parent=None, alignment=None):
        super().__init__()

        # Initialize the PI dictionary (to store data)
        self.pi_data = {}
        self.alignment = alignment

        if hasattr(alignment, 'ModelKeeper'):
            if alignment.ModelKeeper:
                self.pi_data = alignment.ModelKeeper

        # Main layout
        main_layout = QVBoxLayout()

        # Button layout (top buttons)
        top_button_layout = QHBoxLayout()
        self.add_button = QPushButton("New PI")
        self.add_button.clicked.connect(self.add_item)
        self.delete_button = QPushButton("Delete PI")
        self.delete_button.clicked.connect(self.delete_item)

        top_button_layout.addWidget(self.add_button)
        top_button_layout.addWidget(self.delete_button)

        main_layout.addLayout(top_button_layout)

        # Tree view widget
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Attribute", "Value"])
        self.tree_view.setModel(self.model)

        # Set delegate for "Curve Type"
        self.curve_type_delegate = ComboBoxDelegate(["None", "Curve", "Spiral-Curve-Spiral"])
        self.curve_type = {}

        # Add top-level root item
        self.root_node = self.model.invisibleRootItem()

        main_layout.addWidget(self.tree_view)

        # Button layout (bottom buttons)
        bottom_button_layout = QHBoxLayout()
        self.load_csv_button = QPushButton("Load CSV")
        self.load_csv_button.clicked.connect(self.load_csv)
        self.apply_button = QPushButton("Apply")  # Changed from "Save" to "Apply"
        self.apply_button.clicked.connect(self.save_data)

        bottom_button_layout.addWidget(self.load_csv_button)
        bottom_button_layout.addWidget(self.apply_button)

        main_layout.addLayout(bottom_button_layout)
        self.setLayout(main_layout)

        # Load data (from pi_data)
        self.load_data()

    def load_csv(self):
        """Load data from a CSV file and populate the tree."""
        csv_file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if not csv_file_path:
            return  # No file selected

        with open(csv_file_path, "r", newline='', encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=";")
            
            # Clear the tree before loading new data
            self.root_node.removeRows(0, self.root_node.rowCount())

            for row_data in csv_reader:
                self.add_item(row_data)

    def add_item(self, row_data=None):
        """Add a new PI entry to the tree."""
        # Create root item for each PI entry
        pi_item = QStandardItem()
        pi_item.setEditable(False)
        self.root_node.appendRow(pi_item)

        pi_name = row_data[0] if row_data else str(pi_item.index().row() + 1)
        x = row_data[1] if row_data else ""
        y = row_data[2] if row_data else ""
        curve_type = row_data[3] if row_data and len(row_data) > 3 else "None"

        pi_item.setText(pi_name)

        # Create sub-items for each attribute and value
        self._add_attribute_item(pi_item, "X", x)
        self._add_attribute_item(pi_item, "Y", y)
        self._add_curve_type_item(pi_item, "Curve Type", curve_type)

        # Add additional attributes based on Curve Type
        self._update_curve_type(pi_item, curve_type, row_data)

    def _add_attribute_item(self, parent_item, attribute_name, value):
        """Helper method to add an attribute and its value to the tree under the given parent."""
        attribute_item = QStandardItem(attribute_name)
        value_item = QStandardItem(value)
        value_item.setEditable(True)  # Allow editing the value
        parent_item.appendRow([attribute_item, value_item])

    def _add_curve_type_item(self, parent_item, attribute_name, value):
        """Helper method to add a Curve Type attribute with a ComboBox to the tree."""
        attribute_item = QStandardItem(attribute_name)
        value_item = QStandardItem(value)
        parent_item.appendRow([attribute_item, value_item])
        self.curve_type[id(parent_item)] = value

        # Set the delegate only for Curve Type rows
        index = self.model.indexFromItem(value_item)
        self.tree_view.setItemDelegateForRow(index.row(), self.curve_type_delegate)

        # Connect changes to dynamic update
        self.tree_view.model().itemChanged.connect(lambda item: self._handle_curve_type_change(parent_item))

    def _handle_curve_type_change(self, parent_item):
        """Dynamically update the tree based on Curve Type selection."""
        curve_type_item = parent_item.child(2, 1)  # Assuming Curve Type is the third attribute
        curve_type = curve_type_item.text()

        if self.curve_type[id(parent_item)] != curve_type:
            self.curve_type[id(parent_item)] = curve_type

            # Clear existing sub-items for Curve Type
            while parent_item.rowCount() > 3:
                parent_item.removeRow(3)

            self._update_curve_type(parent_item, curve_type)

    def _update_curve_type(self, parent_item, curve_type, row_data=None):
        """Add or remove attributes dynamically based on the Curve Type."""
        if curve_type == "Curve":
            radius = row_data[5] if row_data and len(row_data) > 5 else ""
            self._add_attribute_item(parent_item, "Radius", radius)
        elif curve_type == "Spiral-Curve-Spiral":
            spiral_in = row_data[4] if row_data and len(row_data) > 4 else ""
            radius = row_data[5] if row_data and len(row_data) > 5 else ""
            spiral_out = row_data[6] if row_data and len(row_data) > 6 else ""
            self._add_attribute_item(parent_item, "Spiral Length In", spiral_in)
            self._add_attribute_item(parent_item, "Radius", radius)
            self._add_attribute_item(parent_item, "Spiral Length Out", spiral_out)

    def delete_item(self):
        """Delete the selected item from the tree."""
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            index = selected_indexes[0]
            item = self.model.itemFromIndex(index)

            # Remove the item (if it's a root-level item)
            if item.parent() == None:
                self.root_node.removeRow(item.row())

    def save_data(self):
        """Save entered data to the pi_data dictionary."""
        self.pi_data.clear()

        for row in range(self.root_node.rowCount()):
            item = self.root_node.child(row)
            pi_name = item.text()

            data = {}
            for i in range(item.rowCount()):
                attribute_item = item.child(i, 0)
                value_item = item.child(i, 1)
                data[attribute_item.text()] = value_item.text()

            self.pi_data[pi_name] = data

        if self.alignment:
            self.alignment.ModelKeeper = self.pi_data

    def load_data(self):
        """Load data from the pi_data dictionary into the tree."""
        for pi_name, data in self.pi_data.items():
            self.add_item([
                pi_name,
                data.get("X", ""),
                data.get("Y", ""),
                data.get("Curve Type", "None"),
                data.get("Spiral Length In", ""),
                data.get("Radius", ""),
                data.get("Spiral Length Out", "")
            ])

def run(alignment=None):
    import FreeCADGui
    from .task_panel import TaskPanel
    main_window = FreeCADGui.getMainWindow()
    panel = TaskPanel(PiTreeViewWidget(main_window, alignment))
    return panel
