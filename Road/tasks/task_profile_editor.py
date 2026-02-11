# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the task panel code for edit Profile PVI points tool."""

import FreeCAD
from PySide.QtWidgets import (QVBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem, 
                               QWidget, QHBoxLayout, QFileDialog, QComboBox, QLabel, 
                               QMessageBox, QInputDialog)
from PySide.QtCore import Qt
import csv


class ProfileEditor(QWidget):
    """Tree widget for editing profile PVI (Point of Vertical Intersection) points."""
    
    def __init__(self, alignment):
        super().__init__()
        
        # Store profile reference
        self.alignment = alignment
        self.profiles = alignment.Model.profiles
        
        # Main layout
        main_layout = QVBoxLayout()
        # __init__ metodunda, profile selection combo'nun bulunduğu kısmı güncelleyin:

        # Profile selection combo
        profile_layout = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.currentTextChanged.connect(self.load_data)
        self.create_profile_button = QPushButton("Create Profile")
        self.create_profile_button.clicked.connect(self.create_profile)

        profile_layout.addWidget(self.profile_combo, stretch=1)
        profile_layout.addWidget(self.create_profile_button)
        main_layout.addLayout(profile_layout)

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
        profile_names = self.profiles.get_profalign_names()
        self.profile_combo.addItems(profile_names)
        
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
        # Yeni metot ekleyin:

    def create_profile(self):
        """Create a new profile."""
        
        # Ask for profile name
        profile_name, ok = QInputDialog.getText(
            self, 
            "New Profile", 
            "Enter profile name:",
            text=f"Profile {len(self.profiles.design_profiles) + 1}"
        )
        
        if not ok or not profile_name.strip():
            return
        
        # Check if name already exists
        existing_names = self.profiles.get_profalign_names()
        if profile_name in existing_names:
            QMessageBox.warning(
                self,
                "Name Exists",
                f"A profile named '{profile_name}' already exists."
            )
            return
        
        # Create minimal PVI data (start and end points)
        # Get alignment start and end stations
        start_sta = self.alignment.Model.get_sta_start()
        end_sta = self.alignment.Model.get_sta_end()
        
        # Create default profile data with 2 PVIs
        new_profile_data = [
            {
                'pvi': {
                    'station': start_sta,
                    'elevation': 0.0
                }
            },
            {
                'pvi': {
                    'station': end_sta,
                    'elevation': 0.0
                }
            }
        ]
        
        # Create new Profile object
        from ..geometry.profile.profile import Profile
        new_profile = Profile(
            name=profile_name,
            desc="New design profile",
            data=new_profile_data
        )
        
        # Add to profiles
        self.profiles.design_profiles.append(new_profile)
        
        # Update combo box
        self.profile_combo.blockSignals(True)
        self.profile_combo.addItem(profile_name)
        self.profile_combo.setCurrentText(profile_name)
        self.profile_combo.blockSignals(False)
        
        # Load the new profile
        self.load_data(profile_name)
        
        print(f"New profile '{profile_name}' created successfully")

    def add_pvi(self, pvi_data=None):
        """Add a new PVI point to the tree."""
        # Create root item for PVI
        pvi_index = self.tree_widget.topLevelItemCount() + 1
        pvi_item = QTreeWidgetItem(self.tree_widget)
        pvi_item.setText(0, f"PVI {pvi_index}")
        pvi_item.setFlags(pvi_item.flags() | Qt.ItemIsEditable)
        
        # Get default values
        if pvi_data:
            station = str(pvi_data.get('pvi', {}).get('station', 0.0))
            elevation = str(pvi_data.get('pvi', {}).get('elevation', 0.0))
            curve_type = pvi_data.get('type', '')
            description = pvi_data.get('desc', '')
        else:
            station = "0.0"
            elevation = "0.0"
            curve_type = ""
            description = ""
        
        # Add basic properties
        self._add_property_item(pvi_item, "Station", station, editable=True)
        self._add_property_item(pvi_item, "Elevation", elevation, editable=True)
        self._add_property_item(pvi_item, "Curve Type", curve_type, editable=True)
        
        # Add curve-specific parameters based on type
        if pvi_data:
            if curve_type == "ParaCurve":
                length = str(pvi_data.get('length', ''))
                k_val = str(pvi_data.get('kValue', ''))
                self._add_property_item(pvi_item, "Curve Length", length, editable=True)
                self._add_property_item(pvi_item, "K Value", k_val, editable=True)

            elif curve_type == "UnsymParaCurve":
                length_in = str(pvi_data.get('lengthIn', ''))
                length_out = str(pvi_data.get('lengthOut', ''))
                self._add_property_item(pvi_item, "Length In", length_in, editable=True)
                self._add_property_item(pvi_item, "Length Out", length_out, editable=True)
                
            elif curve_type == "CircCurve":
                length = str(pvi_data.get('length', ''))
                radius = str(pvi_data.get('radius', ''))
                self._add_property_item(pvi_item, "Curve Length", length, editable=True)
                self._add_property_item(pvi_item, "Radius", radius, editable=True)
        
        # Add description
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
        self._add_property_item(pvi_item, "Curve Type", "", editable=True)
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
        
        # Create persistent ComboBox for Curve Type
        if property_name == "Curve Type":
            combo = QComboBox()
            combo.addItems(["", "ParaCurve", "UnsymParaCurve", "CircCurve"])
            # Set current value
            idx = combo.findText(value)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            # Store property item reference for updates
            combo.setProperty("property_item", property_item)
            combo.currentTextChanged.connect(lambda text, item=parent_item: self._update_curve_parameters(item, text))
            self.tree_widget.setItemWidget(property_item, 1, combo)
        
        return property_item

    def _update_curve_parameters(self, pvi_item, curve_type):
        """Update curve parameters based on curve type selection."""
        # Update the Curve Type property value
        for j in range(pvi_item.childCount()):
            child = pvi_item.child(j)
            if child.text(0) == "Curve Type":
                child.setText(1, curve_type)
                break
        
        # Remove existing curve parameter items (except Station, Elevation, Curve Type, Description)
        items_to_remove = []
        for j in range(pvi_item.childCount()):
            child = pvi_item.child(j)
            prop_name = child.text(0)
            if prop_name in ["Curve Length", "K Value", "Length In", "Length Out", "Radius"]:
                items_to_remove.append(j)
        
        # Remove in reverse order to maintain indices
        for idx in reversed(items_to_remove):
            pvi_item.takeChild(idx)
        
        # Add appropriate parameters based on curve type
        # Find insertion point (after Curve Type, before Description)
        insert_index = 0
        for j in range(pvi_item.childCount()):
            if pvi_item.child(j).text(0) == "Curve Type":
                insert_index = j + 1
                break
        
        if curve_type == "ParaCurve":
            # Add Length and K Value parameter
            length_item = QTreeWidgetItem()
            length_item.setText(0, "Curve Length")
            length_item.setText(1, "")
            length_item.setFlags(length_item.flags() | Qt.ItemIsEditable)
            pvi_item.insertChild(insert_index, length_item)
            
            k_value_item = QTreeWidgetItem()
            k_value_item.setText(0, "K Value")
            k_value_item.setText(1, "")
            k_value_item.setFlags(k_value_item.flags() | Qt.ItemIsEditable)
            pvi_item.insertChild(insert_index + 1, k_value_item)
            
        elif curve_type == "UnsymParaCurve":
            # Add Length In and Length Out parameters
            length_in_item = QTreeWidgetItem()
            length_in_item.setText(0, "Length In")
            length_in_item.setText(1, "")
            length_in_item.setFlags(length_in_item.flags() | Qt.ItemIsEditable)
            pvi_item.insertChild(insert_index, length_in_item)
            
            length_out_item = QTreeWidgetItem()
            length_out_item.setText(0, "Length Out")
            length_out_item.setText(1, "")
            length_out_item.setFlags(length_out_item.flags() | Qt.ItemIsEditable)
            pvi_item.insertChild(insert_index + 1, length_out_item)
            
        elif curve_type == "CircCurve":
            # Add Length and Radius parameters
            length_item = QTreeWidgetItem()
            length_item.setText(0, "Curve Length")
            length_item.setText(1, "")
            length_item.setFlags(length_item.flags() | Qt.ItemIsEditable)
            pvi_item.insertChild(insert_index, length_item)
            
            radius_item = QTreeWidgetItem()
            radius_item.setText(0, "Radius")
            radius_item.setText(1, "")
            radius_item.setFlags(radius_item.flags() | Qt.ItemIsEditable)
            pvi_item.insertChild(insert_index + 1, radius_item)
    
    def _renumber_pvis(self):
        """Renumber all PVI items sequentially."""
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            item.setText(0, f"PVI {i + 1}")
    
    def on_item_changed(self, item, column):
        """
        Handle item value changes and validate numeric inputs for profile properties.
        """
        # Only process changes in the 'Value' column
        if column != 1:
            return
        
        property_name = item.text(0)
        value = item.text(1).strip()
        
        # Define fields that must be numeric
        numeric_fields = ["Station", "Elevation", "Curve Length", "K Value", 
                          "Length In", "Length Out", "Radius"]
        
        if property_name in numeric_fields:
            # Allow empty values for optional curve parameters
            if value == "":
                return
            
            try:
                # Attempt to convert the input to a float
                float(value)
            except ValueError:
                # If conversion fails, revert to a safe default
                # Stations and Elevations default to 0.0, others to empty string
                if property_name in ["Station", "Elevation"]:
                    item.setText(1, "0.0")
                else:
                    item.setText(1, "")
                
                # Optional: Show a message to the user
                print(f"Invalid input for {property_name}: {value}. Please enter a numeric value.")

    def load_data(self, profile_name):
        """Load PVI data from self.pvi_data into tree."""
        self.tree_widget.clear()

        # Get selected profile
        self.profile = self.profiles.get_profile_by_name(profile_name)
        
        # Load PVI data
        for pvi_entry in self.profile.data:
            self.add_pvi(pvi_entry)
        
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
                        'pvi': {
                            'station': float(row_data[0]) if row_data[0] else 0.0,
                            'elevation': float(row_data[1]) if row_data[1] else 0.0,
                        },
                        'length': float(row_data[2]) if len(row_data) > 2 and row_data[2] else None,
                        'type': row_data[3] if len(row_data) > 3 else '',
                        'desc': row_data[4] if len(row_data) > 4 else ''
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
                        pvi_data['pvi']['station'],
                        pvi_data['pvi']['elevation'],
                        pvi_data.get('length', ''),
                        pvi_data.get('type', ''),
                        pvi_data.get('desc', '')
                    ])
                    
        except Exception as e:
            print(f"Error saving CSV: {e}")

    def get_pvi_data(self):
        """Extract PVI data from tree widget in format compatible with Profile.data."""
        pvi_list = []
        
        for i in range(self.tree_widget.topLevelItemCount()):
            pvi_item = self.tree_widget.topLevelItem(i)
            
            # Extract property values
            pvi_data = {'pvi': {}}
            
            for j in range(pvi_item.childCount()):
                property_item = pvi_item.child(j)
                property_name = property_item.text(0)
                property_value = property_item.text(1)
                
                if property_name == "Station":
                    pvi_data['pvi']['station'] = float(property_value) if property_value else 0.0
                elif property_name == "Elevation":
                    pvi_data['pvi']['elevation'] = float(property_value) if property_value else 0.0
                elif property_name == "Curve Length":
                    if property_value:
                        pvi_data['length'] = float(property_value)
                elif property_name == "K Value":
                    if property_value:
                        pvi_data['kValue'] = float(property_value)
                elif property_name == "Length In":
                    if property_value:
                        pvi_data['lengthIn'] = float(property_value)
                elif property_name == "Length Out":
                    if property_value:
                        pvi_data['lengthOut'] = float(property_value)
                elif property_name == "Radius":
                    if property_value:
                        pvi_data['radius'] = float(property_value)
                elif property_name == "Curve Type":
                    if property_value:
                        pvi_data['type'] = property_value
                elif property_name == "Description":
                    if property_value:
                        pvi_data['desc'] = property_value
            
            pvi_list.append(pvi_data)
        
        return pvi_list
    
    def apply_changes(self):
        """Apply changes to the profile."""
        # Get PVI data from tree
        pvi_list = self.get_pvi_data()
        
        if len(pvi_list) < 2:
            print("Error: At least 2 PVI points are required")
            return
        
        # If profile reference exists, update it
        if self.profile:
            try:
                # Get the profile object from ProfileFrame
                self.profile.update(pvi_list)
                
                # Trigger ProfileFrame recompute
                for obj in self.alignment.Group:
                    if obj.Proxy.Type == "Road::Profiles":
                        for profile_obj in obj.Group:
                            profile_obj.touch()
                FreeCAD.ActiveDocument.recompute()
                
                print(f"Profile '{self.profile.name}' updated successfully with {len(pvi_list)} PVI points")
                
            except Exception as e:
                print(f"Error updating profile: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("No profile reference available")