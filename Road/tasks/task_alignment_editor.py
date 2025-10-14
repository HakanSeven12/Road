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

import FreeCAD

from PySide.QtWidgets import QVBoxLayout, QPushButton, QTreeView, QWidget, QHBoxLayout
from PySide.QtGui import QStandardItem, QStandardItemModel

class AlignmentEditor(QWidget):
    def __init__(self, parent=None, alignment=None):
        super().__init__()
        self.alignment = alignment
        if not alignment or not hasattr(alignment.Proxy, 'model'):
            print("No alignment or Model attribute found")
            return

        self.geometry = alignment.Proxy.model.geometry
        if not self.geometry:
            print("No model data found")
            return
        
        self.initui()

    def initui(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Button layout (top buttons)
        top_button_layout = QHBoxLayout()
        self.add_button = QPushButton("New Geometry")
        self.add_button.clicked.connect(self.add_item)
        self.delete_button = QPushButton("Delete Geometry")
        self.delete_button.clicked.connect(self.delete_item)

        top_button_layout.addWidget(self.add_button)
        top_button_layout.addWidget(self.delete_button)

        main_layout.addLayout(top_button_layout)

        # Tree view widget
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Attribute", "Value"])
        self.tree_view.setModel(self.model)

        # Add top-level root item
        self.root_node = self.model.invisibleRootItem()
        main_layout.addWidget(self.tree_view)

        # Button layout (bottom buttons)
        bottom_button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.save_data)
        bottom_button_layout.addWidget(self.apply_button)

        main_layout.addLayout(bottom_button_layout)
        self.setLayout(main_layout)

        # Load data (from geometry)
        self.load_data()

    def add_item(self, no, geo):
        """Add a new PI entry to the tree."""
        # Create root item for each PI entry
        geo_item = QStandardItem()
        geo_item.setEditable(False)
        self.root_node.appendRow(geo_item)

        geo_no = str(no)
        geo_item.setText(geo_no)
        #["Type", "Constraint", "Locked", "Parameter", "Length", "Radius", "Direction", "InternalStation", "Delta", "Chord", "Curvature"]:
        for sub in geo:
            val = geo.get(sub)
            if not val: continue
            """
            if sub in ["Length", "Radius", "Chord"]:
                val = round(float(val) / 1000, 3)
            if sub in ["BearingIn", "Delta"]:
                val = round(float(val), 3)
            elif sub == "InternalStation":
                val = [round(float(x) / 1000, 3) for x in val]
            """
            self._add_attribute_item(geo_item, sub, str(val))

        # Expand the newly added item
        index = self.model.indexFromItem(geo_item)
        self.tree_view.expand(index)

    def _add_attribute_item(self, parent_item, attribute_name, value):
        """Helper method to add an attribute and its value to the tree under the given parent."""
        attribute_item = QStandardItem(attribute_name)
        value_item = QStandardItem(value)
        value_item.setEditable(True)  # Allow editing the value
        parent_item.appendRow([attribute_item, value_item])

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
        """Save entered data to the geometry dictionary and update alignment."""
        self.geometry.clear()

        for row in range(self.root_node.rowCount()):
            item = self.root_node.child(row)

            attr = {}
            for i in range(item.rowCount()):
                attribute_item = item.child(i, 0)
                value_item = item.child(i, 1)
                if attribute_item and value_item:
                    try: val = float(value_item.text())
                    except: 
                        try: val = eval(value_item.text())
                        except: val = value_item.text()
                    attr[attribute_item.text()] = val

            self.geometry[row+1] = attr
            print(self.geometry)

            model = self.alignment.Proxy.model
            model.geometry = self.geometry
            model.construct_geometry()
            self.alignment.Shape = model.get_shape()
            pis = model.get_pi_coords()
            self.alignment.PIs = [FreeCAD.Vector(pi) for pi in pis]

    def load_data(self):
        """Load data from the geometry dictionary into the tree."""
        # Clear existing tree data
        self.root_node.removeRows(0, self.root_node.rowCount())
        
        for no, geo in self.geometry.items():
            self.add_item(no, geo)

        # Expand all items by default
        self.tree_view.expandAll()

def run(alignment=None):
    import FreeCADGui
    from .task_panel import TaskPanel
    main_window = FreeCADGui.getMainWindow()
    panel = TaskPanel(AlignmentEditor(main_window, alignment))
    return panel