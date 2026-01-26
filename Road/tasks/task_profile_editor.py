# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the task panel code for edit Profile PVI points tool."""

import FreeCAD
from PySide.QtWidgets import (QVBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem, 
                               QWidget, QHBoxLayout, QFileDialog, QComboBox, QLineEdit,
                               QDoubleSpinBox, QLabel)
from PySide.QtCore import Qt
import csv


class ProfileEditor(QWidget):
    """Tree widget for editing profile PVI (Point of Vertical Intersection) points."""
    
    def __init__(self, parent=None, profile=None):
        super().__init__()
        
        # Store profile reference
        self.profile = profile
        self.pvi_data = []
        
        # Load existing PVI data from profile if available
        if profile and hasattr(profile, 'profalign_list') and profile.profalign_list:
            self.pvi_data = profile.profalign_list[0]['pvi_points'].copy()
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Top button layout
        top_button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add PVI")
        self.add_button.clicked.connect(self.add_pvi)
        self.insert_button = QPushButton("Insert PVI")
        self.insert_button.clicked.connect(self.insert_pvi)
        self.delete_button = QPushButton("Delete PVI")
        self.delete_button.clicked.connect(self.delete_pvi)
        
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
    
    def add_pvi(self, pvi_data=None):
        """Add a new PVI point to the tree."""
        # Create root item for PVI
        pvi_index = self.tree_widget.topLevelItemCount() + 1
        pvi_item = QTreeWidgetItem(self.tree_widget)
        pvi_item.setText(0, f"PVI {pvi_index}")
        pvi_item.setFlags(pvi_item.flags() | Qt.ItemIsEditable)
        
        # Get default values
        if pvi_data:
            station = str(pvi_data.get('station', 0.0))
            elevation = str(pvi_data.get('elevation', 0.0))
            curve_length = str(pvi_data.get('curve_length', ''))
            curve_type = pvi_data.get('curve_type', 'ParaCurve')
            description = pvi_data.get('description', '')
        else:
            station = "0.0"
            elevation = "0.0"
            curve_length = ""
            curve_type = "ParaCurve"
            description = ""
        
        # Add properties
        self._add_property_item(pvi_item, "Station", station, editable=True)
        self._add_property_item(pvi_item, "Elevation", elevation, editable=True)
        self._add_property_item(pvi_item, "Curve Length", curve_length, editable=True)
        self._add_property_item(pvi_item, "Curve Type", curve_type, editable=True)
        self._add_property_item(pvi_item, "Description", description, editable=True)
        
        # Expand the item
        pvi_item.setExpanded(True)
        
        return pvi_item
    
    def insert_pvi(self):
        """Insert a new PVI point before the selected item."""
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            self.add_pvi()
            return
        
        selected_item = selected_items[0]
        
        # Get the parent (should be None for top-level items)
        if selected_item.parent() is not None:
            selected_item = selected_item.parent()
        
        # Get index
        index = self.tree_widget.indexOfTopLevelItem(selected_item)
        
        # Create new PVI item
        pvi_item = QTreeWidgetItem()
        pvi_item.setText(0, f"PVI {index + 1}")
        pvi_item.setFlags(pvi_item.flags() | Qt.ItemIsEditable)
        
        # Add properties with default values
        self._add_property_item(pvi_item, "Station", "0.0", editable=True)
        self._add_property_item(pvi_item, "Elevation", "0.0", editable=True)
        self._add_property_item(pvi_item, "Curve Length", "", editable=True)
        self._add_property_item(pvi_item, "Curve Type", "ParaCurve", editable=True)
        self._add_property_item(pvi_item, "Description", "", editable=True)
        
        # Insert at index
        self.tree_widget.insertTopLevelItem(index, pvi_item)
        
        # Renumber all PVIs
        self._renumber_pvis()
        
        # Expand the item
        pvi_item.setExpanded(True)
    
    def delete_pvi(self):
        """Delete the selected PVI point."""
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            return
        
        selected_item = selected_items[0]
        
        # Get the top-level item (PVI item)
        if selected_item.parent() is not None:
            selected_item = selected_item.parent()
        
        # Get index and remove
        index = self.tree_widget.indexOfTopLevelItem(selected_item)
        self.tree_widget.takeTopLevelItem(index)
        
        # Renumber remaining PVIs
        self._renumber_pvis()
    
    def _add_property_item(self, parent_item, property_name, value, editable=True):
        """Add a property item to a parent PVI item."""
        property_item = QTreeWidgetItem(parent_item)
        property_item.setText(0, property_name)
        property_item.setText(1, value)
        
        if editable:
            property_item.setFlags(property_item.flags() | Qt.ItemIsEditable)
        else:
            property_item.setFlags(property_item.flags() & ~Qt.ItemIsEditable)
        
        return property_item
    
    def _renumber_pvis(self):
        """Renumber all PVI items sequentially."""
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            item.setText(0, f"PVI {i + 1}")
    
    def on_item_changed(self, item, column):
        """Handle item value changes."""
        # Only process value column changes
        if column != 1:
            return
        
        # Validate numeric inputs
        property_name = item.text(0)
        value = item.text(1)
        
        if property_name in ["Station", "Elevation", "Curve Length"]:
            # Allow empty values for optional fields
            if value.strip() == "" and property_name == "Curve Length":
                return
            
            # Validate numeric value
            try:
                float(value)
            except ValueError:
                # Invalid number, revert to previous value or empty
                item.setText(1, "0.0" if property_name != "Curve Length" else "")
    
    def load_data(self):
        """Load PVI data from profile into tree."""
        self.tree_widget.clear()
        
        for pvi_data in self.pvi_data:
            self.add_pvi(pvi_data)
    
    def load_from_csv(self):
        """Load PVI data from CSV file."""
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
                    
                    pvi_data = {
                        'station': float(row_data[0]) if row_data[0] else 0.0,
                        'elevation': float(row_data[1]) if row_data[1] else 0.0,
                        'curve_length': row_data[2] if len(row_data) > 2 else '',
                        'curve_type': row_data[3] if len(row_data) > 3 else 'ParaCurve',
                        'description': row_data[4] if len(row_data) > 4 else ''
                    }
                    
                    self.add_pvi(pvi_data)
                    
        except Exception as e:
            print(f"Error loading CSV: {e}")
    
    def save_to_csv(self):
        """Save PVI data to CSV file."""
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
                    "Station", "Elevation", "Curve Length", "Curve Type", "Description"
                ])
                
                # Write data
                pvi_list = self.get_pvi_data()
                for pvi_data in pvi_list:
                    csv_writer.writerow([
                        pvi_data['station'],
                        pvi_data['elevation'],
                        pvi_data.get('curve_length', ''),
                        pvi_data.get('curve_type', 'ParaCurve'),
                        pvi_data.get('description', '')
                    ])
                    
        except Exception as e:
            print(f"Error saving CSV: {e}")
    
    def get_pvi_data(self):
        """Extract PVI data from tree widget."""
        pvi_list = []
        
        for i in range(self.tree_widget.topLevelItemCount()):
            pvi_item = self.tree_widget.topLevelItem(i)
            
            # Extract property values
            pvi_data = {}
            
            for j in range(pvi_item.childCount()):
                property_item = pvi_item.child(j)
                property_name = property_item.text(0)
                property_value = property_item.text(1)
                
                if property_name == "Station":
                    pvi_data['station'] = float(property_value) if property_value else 0.0
                elif property_name == "Elevation":
                    pvi_data['elevation'] = float(property_value) if property_value else 0.0
                elif property_name == "Curve Length":
                    pvi_data['curve_length'] = float(property_value) if property_value else None
                elif property_name == "Curve Type":
                    pvi_data['curve_type'] = property_value if property_value else 'ParaCurve'
                elif property_name == "Description":
                    pvi_data['description'] = property_value if property_value else None
            
            pvi_list.append(pvi_data)
        
        return pvi_list
    
    def apply_changes(self):
        """Apply changes to the profile."""
        # Get PVI data from tree
        pvi_list = self.get_pvi_data()
        
        if len(pvi_list) < 2:
            print("Error: At least 2 PVI points are required")
            return
        
        # Update profile if available
        if self.profile:
            model = self.profile.Model
            try:
                # Create geometry data for profile reconstruction
                geometry_data = []
                
                # Add PVI points
                for pvi in pvi_list:
                    geometry_data.append({
                        'Type': 'PVI',
                        'station': pvi['station'],
                        'elevation': pvi['elevation'],
                        'desc': pvi.get('description', None)
                    })
                
                # Add curves between PVIs
                for i in range(len(pvi_list) - 1):
                    curr_pvi = pvi_list[i]
                    next_pvi = pvi_list[i + 1]
                    
                    # If curve length is specified, add curve at current PVI
                    if curr_pvi.get('curve_length') and i > 0:
                        curve_data = {
                            'Type': curr_pvi.get('curve_type', 'ParaCurve'),
                            'length': curr_pvi['curve_length'],
                            'pvi': {
                                'station': curr_pvi['station'],
                                'elevation': curr_pvi['elevation']
                            }
                        }
                        geometry_data.append(curve_data)
                
                # Reconstruct profile with new geometry
                from Road.geometry.profile.profile import Profile
                
                profile_data = {
                    'name': model.name,
                    'staStart': pvi_list[0]['station'],
                    'staEnd': pvi_list[-1]['station'],
                    'ProfAlign': {
                        'name': model.profalign_list[0]['name'] if model.profalign_list else 'Design Profile',
                        'staStart': pvi_list[0]['station'],
                        'length': pvi_list[-1]['station'] - pvi_list[0]['station'],
                        'geometry': geometry_data
                    }
                }
                
                # Create new profile
                self.profile.Model = Profile(profile_data, model.parent_alignment)
                
                print("Profile updated successfully")
                
            except Exception as e:
                print(f"Error updating profile: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("No profile reference available")
        
        FreeCAD.ActiveDocument.recompute()