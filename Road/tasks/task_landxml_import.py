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
        self.tree.setHeaderLabels(['Item', 'Type', 'Detail'])
        self.tree.setSelectionMode(QTreeWidget.MultiSelection)
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
        root_item.setText(1, 'Root')
        root_item.setExpanded(True)
        
        # Add metadata information
        self._add_metadata_items(root_item, tree_data['metadata'])
        
        # Surfaces
        self._add_surfaces_items(root_item, tree_data['surfaces'])
        
        # Alignments
        self._add_alignments_items(root_item, tree_data['alignments'])
        
    def _add_metadata_items(self, root_item, metadata):
        """Adds metadata items to the tree."""
        # Units
        if metadata['units']:
            units_item = QTreeWidgetItem(root_item)
            units_item.setText(0, 'Units')
            units_item.setText(1, 'Units')
            
            for attr, value in metadata['units'].items():
                attr_item = QTreeWidgetItem(units_item)
                attr_item.setText(0, attr)
                attr_item.setText(2, str(value))
                attr_item.setFlags(attr_item.flags() & ~Qt.ItemIsSelectable)
                
        # Project
        if metadata['project']:
            proj_item = QTreeWidgetItem(root_item)
            proj_item.setText(0, f"Project: {metadata['project']['name']}")
            proj_item.setText(1, 'Project')
            proj_item.setFlags(proj_item.flags() & ~Qt.ItemIsSelectable)
            
        # Application
        if metadata['application']:
            app_item = QTreeWidgetItem(root_item)
            app_name = metadata['application']['name']
            app_desc = metadata['application']['description']
            app_item.setText(0, f"Application: {app_name}")
            app_item.setText(1, 'Application')
            app_item.setText(2, app_desc)
            app_item.setFlags(app_item.flags() & ~Qt.ItemIsSelectable)
            
    def _add_surfaces_items(self, root_item, surfaces):
        """Adds surface items to the tree."""
        if not surfaces:
            return
            
        surfaces_item = QTreeWidgetItem(root_item)
        surfaces_item.setText(0, 'Surfaces')
        surfaces_item.setText(1, 'Category')
        surfaces_item.setExpanded(True)
        surfaces_item.setFlags(surfaces_item.flags() & ~Qt.ItemIsSelectable)
        
        for surface in surfaces:
            surf_item = QTreeWidgetItem(surfaces_item)
            surf_item.setText(0, surface['name'])
            surf_item.setText(1, 'Surface')
            surf_item.setText(2, f"Surface - {surface['name']}")
            surf_item.setData(0, Qt.UserRole, surface)
            
    def _add_alignments_items(self, root_item, alignments):
        """Adds alignment items to the tree."""
        if not alignments:
            return
            
        alignments_item = QTreeWidgetItem(root_item)
        alignments_item.setText(0, 'Alignments')
        alignments_item.setText(1, 'Category')
        alignments_item.setExpanded(True)
        alignments_item.setFlags(alignments_item.flags() & ~Qt.ItemIsSelectable)
        
        for alignment in alignments:
            align_item = QTreeWidgetItem(alignments_item)
            align_item.setText(0, alignment['name'])
            align_item.setText(1, 'Alignment')
            align_item.setText(2, f"Alignment - {alignment['name']}")
            align_item.setData(0, Qt.UserRole, alignment)
            
    def process_selected(self):
        """Processes the selected items."""
        print("Processing selected items...")
        selected_items = self.tree.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self.form, 'Warning', 'Please select at least one item!')
            return
            
        # Collect data of selected items
        items_to_process = []
        for item in selected_items:
            data = item.data(0, Qt.UserRole)
            if data:  # Only take items containing data
                items_to_process.append(data)
        
        if not items_to_process:
            QMessageBox.warning(self.form, 'Warning', 'No processable items found among the selected ones!')
            return
            
        # Process items with parser
        results = self.parser.process_selected_items(items_to_process)
        
        # Show results
        self._show_results(results)
        
    def _show_results(self, results):
        """Shows the processing results to the user."""
        surfaces_count = results['surfaces_processed']
        alignments_count = results['alignments_processed']
        errors = results['errors']
        
        message = f'{surfaces_count} surfaces and {alignments_count} alignments have been imported into FreeCAD!'
        
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
