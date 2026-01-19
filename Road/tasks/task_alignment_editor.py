# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the task panel code for edit Alignment PI points tool."""

import FreeCAD
from PySide.QtWidgets import (QVBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem, 
                               QWidget, QHBoxLayout, QFileDialog, QComboBox, QLineEdit,
                               QDoubleSpinBox, QLabel)
from PySide.QtCore import Qt
import csv


class AlignmentEditor(QWidget):
    """Tree widget for editing alignment PI (Point of Intersection) points."""
    
    def __init__(self, parent=None, alignment=None):
        super().__init__()
        
        # Store alignment reference
        self.alignment = alignment
        self.pi_data = []
        
        # Load existing PI data from alignment if available
        if alignment and hasattr(alignment, 'align_pis'):
            self.pi_data = alignment.align_pis.copy()
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Top button layout
        top_button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add PI")
        self.add_button.clicked.connect(self.add_pi)
        self.insert_button = QPushButton("Insert PI")
        self.insert_button.clicked.connect(self.insert_pi)
        self.delete_button = QPushButton("Delete PI")
        self.delete_button.clicked.connect(self.delete_pi)
        
        top_button_layout.addWidget(self.add_button)
        top_button_layout.addWidget(self.insert_button)
        top_button_layout.addWidget(self.delete_button)
        
        main_layout.addLayout(top_button_layout)
        
        # Tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Property", "Value"])
        self.tree_widget.setColumnWidth(0, 150)
        self.tree_widget.itemChanged.connect(self.on_item_changed)
        
        main_layout.addWidget(self.tree_widget)
        
        # Bottom button layout
        bottom_button_layout = QHBoxLayout()
        self.load_csv_button = QPushButton("Load from CSV")
        self.load_csv_button.clicked.connect(self.load_from_csv)
        self.save_csv_button = QPushButton("Save to CSV")
        self.save_csv_button.clicked.connect(self.save_to_csv)
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_changes)
        
        bottom_button_layout.addWidget(self.load_csv_button)
        bottom_button_layout.addWidget(self.save_csv_button)
        bottom_button_layout.addWidget(self.apply_button)
        
        main_layout.addLayout(bottom_button_layout)
        self.setLayout(main_layout)
        
        # Load existing data
        self.load_data()
    
    def add_pi(self, pi_data=None):
        """Add a new PI point to the tree."""
        # Create root item for PI
        pi_index = self.tree_widget.topLevelItemCount() + 1
        pi_item = QTreeWidgetItem(self.tree_widget)
        pi_item.setText(0, f"PI {pi_index}")
        pi_item.setFlags(pi_item.flags() | Qt.ItemIsEditable)
        
        # Get default values
        if pi_data:
            point_x = str(pi_data.get('point', (0.0, 0.0))[0])
            point_y = str(pi_data.get('point', (0.0, 0.0))[1])
            spiral_in = str(pi_data.get('spiral_in', ''))
            radius = str(pi_data.get('radius', ''))
            spiral_out = str(pi_data.get('spiral_out', ''))
        else:
            point_x = "0.0"
            point_y = "0.0"
            radius = ""
            spiral_in = ""
            spiral_out = ""
        
        # Add properties
        self._add_property_item(pi_item, "Point X", point_x, editable=True)
        self._add_property_item(pi_item, "Point Y", point_y, editable=True)
        self._add_property_item(pi_item, "Spiral In", spiral_in, editable=True)
        self._add_property_item(pi_item, "Radius", radius, editable=True)
        self._add_property_item(pi_item, "Spiral Out", spiral_out, editable=True)
        
        # Expand the item
        pi_item.setExpanded(True)
        
        return pi_item
    
    def insert_pi(self):
        """Insert a new PI point before the selected item."""
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            self.add_pi()
            return
        
        selected_item = selected_items[0]
        
        # Get the parent (should be None for top-level items)
        if selected_item.parent() is not None:
            selected_item = selected_item.parent()
        
        # Get index
        index = self.tree_widget.indexOfTopLevelItem(selected_item)
        
        # Create new PI item
        pi_item = QTreeWidgetItem()
        pi_item.setText(0, f"PI {index + 1}")
        pi_item.setFlags(pi_item.flags() | Qt.ItemIsEditable)
        
        # Add properties with default values
        self._add_property_item(pi_item, "Point X", "0.0", editable=True)
        self._add_property_item(pi_item, "Point Y", "0.0", editable=True)
        self._add_property_item(pi_item, "Spiral In", "", editable=True)
        self._add_property_item(pi_item, "Radius", "", editable=True)
        self._add_property_item(pi_item, "Spiral Out", "", editable=True)
        
        # Insert at index
        self.tree_widget.insertTopLevelItem(index, pi_item)
        
        # Renumber all PIs
        self._renumber_pis()
        
        # Expand the item
        pi_item.setExpanded(True)
    
    def delete_pi(self):
        """Delete the selected PI point."""
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            return
        
        selected_item = selected_items[0]
        
        # Get the top-level item (PI item)
        if selected_item.parent() is not None:
            selected_item = selected_item.parent()
        
        # Get index and remove
        index = self.tree_widget.indexOfTopLevelItem(selected_item)
        self.tree_widget.takeTopLevelItem(index)
        
        # Renumber remaining PIs
        self._renumber_pis()
    
    def _add_property_item(self, parent_item, property_name, value, editable=True):
        """Add a property item to a parent PI item."""
        property_item = QTreeWidgetItem(parent_item)
        property_item.setText(0, property_name)
        property_item.setText(1, value)
        
        if editable:
            property_item.setFlags(property_item.flags() | Qt.ItemIsEditable)
        else:
            property_item.setFlags(property_item.flags() & ~Qt.ItemIsEditable)
        
        return property_item
    
    def _renumber_pis(self):
        """Renumber all PI items sequentially."""
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            item.setText(0, f"PI {i + 1}")
    
    def on_item_changed(self, item, column):
        """Handle item value changes."""
        # Only process value column changes
        if column != 1:
            return
        
        # Validate numeric inputs
        property_name = item.text(0)
        value = item.text(1)
        
        if property_name in ["Point X", "Point Y", "Station", "Spiral In", "Radius", "Spiral Out"]:
            # Allow empty values
            if value.strip() == "":
                return
            
            # Validate numeric value
            try:
                float(value)
            except ValueError:
                # Invalid number, revert to previous value or empty
                item.setText(1, "")
    
    def load_data(self):
        """Load PI data from alignment into tree."""
        self.tree_widget.clear()
        
        for pi_data in self.pi_data:
            self.add_pi(pi_data)
    
    def load_from_csv(self):
        """Load PI data from CSV file."""
        csv_file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not csv_file_path:
            return
        
        try:
            with open(csv_file_path, "r", newline='', encoding="utf-8") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=";")
                
                # Clear existing data
                self.tree_widget.clear()
                
                # Read header (optional)
                header = next(csv_reader, None)
                
                # Read data rows
                for row_data in csv_reader:
                    if len(row_data) < 2:
                        continue
                    
                    pi_data = {
                        'point': (float(row_data[0]) if row_data[0] else 0.0,
                                 float(row_data[1]) if row_data[1] else 0.0),
                        'station': row_data[2] if len(row_data) > 2 else '',
                        'radius': row_data[3] if len(row_data) > 3 else '',
                        'spiral_in': row_data[4] if len(row_data) > 4 else '',
                        'spiral_out': row_data[5] if len(row_data) > 5 else '',
                        'description': row_data[6] if len(row_data) > 6 else ''
                    }
                    
                    self.add_pi(pi_data)
                    
        except Exception as e:
            print(f"Error loading CSV: {e}")
    
    def save_to_csv(self):
        """Save PI data to CSV file."""
        csv_file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not csv_file_path:
            return
        
        try:
            with open(csv_file_path, "w", newline='', encoding="utf-8") as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=";")
                
                # Write header
                csv_writer.writerow([
                    "Point X", "Point Y", "Station", "Radius", 
                    "Spiral In", "Spiral Out", "Description"
                ])
                
                # Write data
                pi_list = self.get_pi_data()
                for pi_data in pi_list:
                    csv_writer.writerow([
                        pi_data['point'][0],
                        pi_data['point'][1],
                        pi_data.get('station', ''),
                        pi_data.get('radius', ''),
                        pi_data.get('spiral_in', ''),
                        pi_data.get('spiral_out', ''),
                        pi_data.get('description', '')
                    ])
                    
        except Exception as e:
            print(f"Error saving CSV: {e}")
    
    def get_pi_data(self):
        """Extract PI data from tree widget."""
        pi_list = []
        
        for i in range(self.tree_widget.topLevelItemCount()):
            pi_item = self.tree_widget.topLevelItem(i)
            
            # Extract property values
            pi_data = {}
            
            for j in range(pi_item.childCount()):
                property_item = pi_item.child(j)
                property_name = property_item.text(0)
                property_value = property_item.text(1)
                
                if property_name == "Point X":
                    x = float(property_value) if property_value else 0.0
                    pi_data['point'] = (x, pi_data.get('point', (0.0, 0.0))[1])
                elif property_name == "Point Y":
                    y = float(property_value) if property_value else 0.0
                    pi_data['point'] = (pi_data.get('point', (0.0, 0.0))[0], y)
                elif property_name == "Station":
                    pi_data['station'] = float(property_value) if property_value else None
                elif property_name == "Spiral In":
                    pi_data['spiral_in'] = float(property_value) if property_value else None
                elif property_name == "Radius":
                    pi_data['radius'] = float(property_value) if property_value else None
                elif property_name == "Spiral Out":
                    pi_data['spiral_out'] = float(property_value) if property_value else None
                elif property_name == "Description":
                    pi_data['description'] = property_value if property_value else None
            
            pi_list.append(pi_data)
        
        return pi_list
    
    def apply_changes(self):
        """Apply changes to the alignment."""
        # Get PI data from tree
        pi_list = self.get_pi_data()
        
        if len(pi_list) < 2:
            print("Error: At least 2 PI points are required")
            return
        
        # Update alignment if available
        if self.alignment:
            model = self.alignment.Model
            try:
                # Create new alignment from PI points
                from Road.geometry.alignment.alignment import Alignment
                
                alignment_data = {
                    'name': model.name if hasattr(model, 'name') else 'Alignment',
                    'staStart': model.sta_start if hasattr(model, 'sta_start') else 0.0,
                    'AlignPIs': pi_list
                }
                
                # Generate geometry from PIs
                self.alignment.Model = Alignment.from_pis(
                    pi_list,
                    name=alignment_data['name'],
                    sta_start=alignment_data['staStart']
                )
                
                print("Alignment updated successfully")
                
            except Exception as e:
                print(f"Error updating alignment: {e}")
        else:
            print("No alignment reference available")
        FreeCAD.ActiveDocument.recompute()
    
def run(alignment=None):
    """Run the PI editor task panel."""
    import FreeCADGui
    from .task_panel import TaskPanel
    main_window = FreeCADGui.getMainWindow()
    panel = TaskPanel(AlignmentEditor(main_window, alignment))
    return panel