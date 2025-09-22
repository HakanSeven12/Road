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

"""Provides the task panel code for the LandXML Importer tool."""

import FreeCAD, FreeCADGui

from .task_panel import TaskPanel
from ..functions.landxml import LandXMLParser

from PySide.QtWidgets import (QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTreeWidget, 
                             QTreeWidgetItem, QFileDialog, QMessageBox)
from PySide.QtCore import Qt


class TaskLandXMLImport(TaskPanel):
    def __init__(self):
        super().__init__()
        self.form = QWidget()
        self.parser = LandXMLParser()
        self.selected_file = None
        self.initUI()
        
    def initUI(self):
        main_layout = QVBoxLayout(self.form)
        
        # Top section - File selection
        top_layout = QHBoxLayout()
        
        # Left side - File name label
        self.file_label = QLabel('No file selected')
        top_layout.addWidget(self.file_label)
        top_layout.addStretch()
        
        # Right side - Browse button
        self.browse_btn = QPushButton('Browse')
        self.browse_btn.clicked.connect(self.browse_file)
        top_layout.addWidget(self.browse_btn)
        
        main_layout.addLayout(top_layout)
        
        # Middle TreeView
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Item', 'Detail'])
        # Use NoSelection instead of MultiSelection, since we are using checkboxes
        self.tree.setSelectionMode(QTreeWidget.NoSelection)
        # Connect signal to listen for checkbox state changes
        self.tree.itemChanged.connect(self.on_item_changed)
        main_layout.addWidget(self.tree)
        
    def browse_file(self):
        """Opens file selection dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.form, 
            'Select LandXML File', 
            '', 
            'LandXML Files (*.xml);;All Files (*.*)'
        )
        
        if file_path:
            self.selected_file = file_path
            # Show only file name
            file_name = file_path.split('/')[-1]
            self.file_label.setText(file_name)
            self.load_landxml(file_path)
            
    def load_landxml(self, file_path):
        """Loads LandXML file and populates the tree."""
        try:
            # Load file using parser
            if not self.parser.load_file(file_path):
                QMessageBox.critical(self.form, 'Error', 'File could not be loaded!')
                return
            
            # Clear TreeWidget and populate
            self.tree.clear()
            self._populate_tree()
            
        except Exception as e:
            QMessageBox.critical(self.form, 'Error', f'An error occurred while loading the file:\n{str(e)}')
            
    def _populate_tree(self):
        """Populates tree with data from parser."""
        tree_data = self.parser.get_tree_data()
        
        # Root item - LandXML
        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, 'LandXML')
        root_item.setText(1, 'Root Document')
        root_item.setExpanded(True)
        # Add checkbox for root
        root_item.setCheckState(0, Qt.Unchecked)
        root_item.setFlags(root_item.flags() | Qt.ItemIsUserCheckable)
        
        # Add metadata information
        self._add_metadata_items(root_item, tree_data['metadata'])
        
        # Surfaces
        self._add_surfaces_items(root_item, tree_data['surfaces'])
        
        # Alignments
        self._add_alignments_items(root_item, tree_data['alignments'])
        
        # CogoPoints - newly added section
        self._add_cogo_points_items(root_item, tree_data['cogo_points'])
        
    def _add_metadata_items(self, root_item, metadata):
        """Adds metadata items to the tree."""
        # Units
        if metadata['units']:
            units_item = QTreeWidgetItem(root_item)
            units_item.setText(0, 'Units')
            units_item.setText(1, 'Document Units Information')
            
            for attr, value in metadata['units'].items():
                attr_item = QTreeWidgetItem(units_item)
                attr_item.setText(0, attr)
                attr_item.setText(1, str(value))
                attr_item.setFlags(attr_item.flags() & ~Qt.ItemIsSelectable)
                
        # Project
        if metadata['project']:
            proj_item = QTreeWidgetItem(root_item)
            proj_item.setText(0, f"Project: {metadata['project']['name']}")
            proj_item.setText(1, 'Project Information')
            proj_item.setFlags(proj_item.flags() & ~Qt.ItemIsSelectable)
            
        # Application
        if metadata['application']:
            app_item = QTreeWidgetItem(root_item)
            app_name = metadata['application']['name']
            app_desc = metadata['application']['description']
            app_item.setText(0, f"Application: {app_name}")
            app_item.setText(1, app_desc)
            app_item.setFlags(app_item.flags() & ~Qt.ItemIsSelectable)
            
    def _add_surfaces_items(self, root_item, surfaces):
        """Adds surface items to the tree."""
        if not surfaces:
            return
            
        surfaces_item = QTreeWidgetItem(root_item)
        surfaces_item.setText(0, 'Surfaces')
        surfaces_item.setText(1, 'Terrain Surfaces')
        surfaces_item.setExpanded(True)
        # Add checkbox for group
        surfaces_item.setCheckState(0, Qt.Unchecked)
        surfaces_item.setFlags(surfaces_item.flags() | Qt.ItemIsUserCheckable)
        
        for surface in surfaces:
            surf_item = QTreeWidgetItem(surfaces_item)
            surf_item.setText(0, surface['name'])
            surf_item.setText(1, f"Surface - {surface['name']}")
            surf_item.setData(0, Qt.UserRole, surface)
            # Add checkbox
            surf_item.setCheckState(0, Qt.Unchecked)
            surf_item.setFlags(surf_item.flags() | Qt.ItemIsUserCheckable)
            
    def _add_alignments_items(self, root_item, alignments):
        """Adds alignment items to the tree."""
        if not alignments:
            return
            
        alignments_item = QTreeWidgetItem(root_item)
        alignments_item.setText(0, 'Alignments')
        alignments_item.setText(1, 'Road Alignments')
        alignments_item.setExpanded(True)
        # Add checkbox for group
        alignments_item.setCheckState(0, Qt.Unchecked)
        alignments_item.setFlags(alignments_item.flags() | Qt.ItemIsUserCheckable)
        
        for alignment in alignments:
            align_item = QTreeWidgetItem(alignments_item)
            align_item.setText(0, alignment['name'])
            align_item.setText(1, f"Alignment - {alignment['name']}")
            align_item.setData(0, Qt.UserRole, alignment)
            # Add checkbox
            align_item.setCheckState(0, Qt.Unchecked)
            align_item.setFlags(align_item.flags() | Qt.ItemIsUserCheckable)

    def _add_cogo_points_items(self, root_item, cogo_points):
        """Adds CogoPoints items to the tree."""
        if not cogo_points:
            return
            
        cogo_points_item = QTreeWidgetItem(root_item)
        cogo_points_item.setText(0, 'CogoPoints')
        cogo_points_item.setText(1, 'Survey Points')
        cogo_points_item.setExpanded(True)
        # Add checkbox for group
        cogo_points_item.setCheckState(0, Qt.Unchecked)
        cogo_points_item.setFlags(cogo_points_item.flags() | Qt.ItemIsUserCheckable)
        
        for cogo_group in cogo_points:
            # CogoPoints group
            group_item = QTreeWidgetItem(cogo_points_item)
            group_item.setText(0, cogo_group['name'])
            group_item.setText(1, f"Points: {len(cogo_group['points'])}")
            group_item.setData(0, Qt.UserRole, cogo_group)
            group_item.setExpanded(True)
            # Add checkbox
            group_item.setCheckState(0, Qt.Unchecked)
            group_item.setFlags(group_item.flags() | Qt.ItemIsUserCheckable)
            
            # Add each point inside the group as child items
            for point in cogo_group['points']:
                point_item = QTreeWidgetItem(group_item)
                point_item.setText(0, point['name'])
                
                # Point details
                details = []
                if 'x' in point and 'y' in point and 'z' in point:
                    details.append(f"X:{point['x']:.3f}")
                    details.append(f"Y:{point['y']:.3f}")
                    details.append(f"Z:{point['z']:.3f}")
                if point.get('code'):
                    details.append(f"Code:{point['code']}")
                if point.get('desc'):
                    details.append(f"Desc:{point['desc']}")
                    
                point_item.setText(1, " | ".join(details))
                # Individual points cannot be selected, only groups can
                point_item.setFlags(point_item.flags() & ~Qt.ItemIsSelectable)  
            
    def on_item_changed(self, item, column):
        """Handles checkbox state changes."""
        if column != 0:  # Only listen to checkboxes in the first column
            return
            
        # Temporarily block signals to avoid infinite recursion
        self.tree.blockSignals(True)
        
        try:
            # If the item is a group header (Surfaces, Alignments, CogoPoints), update children
            if self._is_group_header(item):
                new_state = item.checkState(0)
                self._update_children_checkboxes(item, new_state)
            
            # If it is a child item, update the parent state
            else:
                self._update_parent_checkbox(item)
                
        finally:
            # Re-enable signals
            self.tree.blockSignals(False)
    
    def _is_group_header(self, item):
        """Checks if the item is a group header."""
        item_text = item.text(0)
        return item_text in ['LandXML', 'Surfaces', 'Alignments', 'CogoPoints']
    
    def _update_children_checkboxes(self, parent_item, state):
        """Updates the checkboxes of child items based on the parent's state."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            # Only update items that have checkboxes
            if child.flags() & Qt.ItemIsUserCheckable:
                child.setCheckState(0, state)
                # If the child itself has children, update them too
                self._update_children_checkboxes(child, state)
    
    def _update_parent_checkbox(self, item):
        """Updates the parent's checkbox state based on its children's states."""
        parent = item.parent()
        if parent is None or not (parent.flags() & Qt.ItemIsUserCheckable):
            return
        
        checked_count = 0
        total_count = 0
        partially_checked = False
        
        # Check all children of the parent
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.flags() & Qt.ItemIsUserCheckable:
                total_count += 1
                child_state = child.checkState(0)
                if child_state == Qt.Checked:
                    checked_count += 1
                elif child_state == Qt.PartiallyChecked:
                    partially_checked = True
        
        # Determine parent state
        if checked_count == 0 and not partially_checked:
            parent.setCheckState(0, Qt.Unchecked)
        elif checked_count == total_count and not partially_checked:
            parent.setCheckState(0, Qt.Checked)
        else:
            parent.setCheckState(0, Qt.PartiallyChecked)
        
        # Recursively update higher-level parents
        self._update_parent_checkbox(parent)
        
    def process_selected(self):
        """Processes the checked items."""
        print("Processing checked items...")
        
        # Collect checked items
        items_to_process = []
        self._collect_checked_items(self.tree.invisibleRootItem(), items_to_process)
        
        if not items_to_process:
            QMessageBox.warning(self.form, 'Warning', 'Please check at least one item!')
            return
            
        # Process items with parser
        results = self.parser.process_selected_items(items_to_process)
        
        # Show results
        self._show_results(results)
        
    def _collect_checked_items(self, parent_item, items_list):
        """Recursively collects checked items."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            
            # If checkbox is checked and item has data, add it
            if (child.checkState(0) == Qt.Checked and 
                child.data(0, Qt.UserRole) is not None):
                items_list.append(child.data(0, Qt.UserRole))
            
            # Check child items as well
            self._collect_checked_items(child, items_list)
        
    def _show_results(self, results):
        """Shows the processing results to the user."""
        surfaces_count = results['surfaces_processed']
        alignments_count = results['alignments_processed']
        cogo_points_count = results['cogo_points_processed']  # CogoPoints count added
        errors = results['errors']
        
        # Build result message
        message_parts = []
        if surfaces_count > 0:
            message_parts.append(f'{surfaces_count} surface(s)')
        if alignments_count > 0:
            message_parts.append(f'{alignments_count} alignment(s)')
        if cogo_points_count > 0:
            message_parts.append(f'{cogo_points_count} CogoPoint(s)')
            
        if message_parts:
            message = ', '.join(message_parts) + ' have been imported into FreeCAD!'
        else:
            message = 'No items were processed.'
        
        if errors:
            message += f'\n\nErrors:\n' + '\n'.join(errors)
            QMessageBox.warning(self.form, 'Warning', message)
        else:
            QMessageBox.information(self.form, 'Success', message)
    
    def accept(self):
        """Accept and process the selected files for import."""
        self.process_selected()
        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()

    def needsFullSpace(self):
        return True
