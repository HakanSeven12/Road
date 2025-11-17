# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the task panel code for the LandXML Importer tool."""

import FreeCAD, FreeCADGui

from .task_panel import TaskPanel
from ..functions.xml.parser import Parser
from ..make import make_terrain, make_alignment, make_geopoints, make_geopoints
from ..functions.alignment.alignment_model import AlignmentModel

from PySide.QtWidgets import (QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTreeWidget, 
                             QTreeWidgetItem, QFileDialog, QMessageBox)
from PySide.QtCore import Qt


class TaskLandXMLImport(TaskPanel):
    def __init__(self):
        super().__init__()
        self.form = QWidget()
        self.parser = Parser()
        self.selected_file = None
        self.errors = []
        self.initUI()
        
    def initUI(self):
        main_layout = QVBoxLayout(self.form)
        
        # Top section - File selection
        top_layout = QHBoxLayout()
        
        self.file_label = QLabel('No file selected')
        top_layout.addWidget(self.file_label)
        top_layout.addStretch()
        
        self.browse_btn = QPushButton('Browse')
        self.browse_btn.clicked.connect(self.browse_file)
        top_layout.addWidget(self.browse_btn)
        
        main_layout.addLayout(top_layout)
        
        # Middle TreeView
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Item'])  # Only one column now
        self.tree.setSelectionMode(QTreeWidget.NoSelection)
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
            file_name = file_path.split('/')[-1]
            self.file_label.setText(file_name)
            self.load_landxml(file_path)
            
    def load_landxml(self, file_path):
        """Loads LandXML file and populates the tree."""
        self.xml = self.parser.load_file(file_path)
        if self.parser.errors:
            for error in self.parser.errors:
                print(error)
            return
        
        self.tree.clear()
        self._populate_tree(self.xml)
            
    def _populate_tree(self, tree_data):
        """Populates tree with data from parser."""
        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, 'LandXML')
        root_item.setExpanded(True)
        root_item.setCheckState(0, Qt.Unchecked)
        root_item.setFlags(root_item.flags() | Qt.ItemIsUserCheckable)
        
        #self._add_metadata_items(root_item, tree_data['metadata'])
        self._add_cogo_points_items(root_item, tree_data['CgPoints'])
        self._add_surfaces_items(root_item, tree_data['Surfaces'])
        self._add_alignments_items(root_item, tree_data['Alignments'])
        
    def _add_metadata_items(self, root_item, metadata):
        """Adds metadata items to the tree."""
        if metadata['units']:
            units_item = QTreeWidgetItem(root_item)
            units_item.setText(0, 'Units')
            units_item.setExpanded(False)
            
            for attr, value in metadata['units'].items():
                attr_item = QTreeWidgetItem(units_item)
                attr_item.setText(0, f"{attr}: {value}")
                attr_item.setFlags(attr_item.flags() & ~Qt.ItemIsSelectable)
                
        if metadata['project']:
            proj_item = QTreeWidgetItem(root_item)
            proj_item.setText(0, f"Project: {metadata['project']['name']}")
            proj_item.setExpanded(False)
            proj_item.setFlags(proj_item.flags() & ~Qt.ItemIsSelectable)
            
        if metadata['application']:
            app_item = QTreeWidgetItem(root_item)
            app_name = metadata['application']['name']
            app_desc = metadata['application']['description']
            app_item.setText(0, f"Application: {app_name} {app_desc}")
            app_item.setExpanded(False)
            app_item.setFlags(app_item.flags() & ~Qt.ItemIsSelectable)
            
    def _add_cogo_points_items(self, root_item, cogo_points):
        """Adds CogoPoints items to the tree."""
        if not cogo_points:
            return
            
        cogo_points_item = QTreeWidgetItem(root_item)
        cogo_points_item.setText(0, 'CogoPoints')
        cogo_points_item.setExpanded(False)
        cogo_points_item.setCheckState(0, Qt.Unchecked)
        cogo_points_item.setFlags(cogo_points_item.flags() | Qt.ItemIsUserCheckable)
        
        for group in cogo_points["Groups"].keys():
            group_item = QTreeWidgetItem(cogo_points_item)
            group_item.setText(0, group)
            group_item.setData(0, Qt.UserRole, group)
            group_item.setCheckState(0, Qt.Unchecked)
            group_item.setFlags(group_item.flags() | Qt.ItemIsUserCheckable)
            
    def _add_surfaces_items(self, root_item, surfaces):
        """Adds surface items to the tree."""
        if not surfaces:
            return
            
        surfaces_item = QTreeWidgetItem(root_item)
        surfaces_item.setText(0, 'Surfaces')
        surfaces_item.setExpanded(False)
        surfaces_item.setCheckState(0, Qt.Unchecked)
        surfaces_item.setFlags(surfaces_item.flags() | Qt.ItemIsUserCheckable)
        
        for surface in surfaces.keys():
            surf_item = QTreeWidgetItem(surfaces_item)
            surf_item.setText(0, surface)
            surf_item.setData(0, Qt.UserRole, surface)
            surf_item.setCheckState(0, Qt.Unchecked)
            surf_item.setFlags(surf_item.flags() | Qt.ItemIsUserCheckable)
            
    def _add_alignments_items(self, root_item, alignments):
        """Adds alignment items to the tree."""
        if not alignments:
            return
            
        alignments_item = QTreeWidgetItem(root_item)
        alignments_item.setText(0, 'Alignments')
        alignments_item.setExpanded(False)
        alignments_item.setCheckState(0, Qt.Unchecked)
        alignments_item.setFlags(alignments_item.flags() | Qt.ItemIsUserCheckable)
        
        for alignment in alignments.keys():
            align_item = QTreeWidgetItem(alignments_item)
            align_item.setText(0, alignment)
            align_item.setData(0, Qt.UserRole, alignment)
            align_item.setCheckState(0, Qt.Unchecked)
            align_item.setFlags(align_item.flags() | Qt.ItemIsUserCheckable)

    def on_item_changed(self, item, column):
        """Handles checkbox state changes."""
        if column != 0:
            return
            
        self.tree.blockSignals(True)
        
        try:
            if self._is_group_header(item):
                new_state = item.checkState(0)
                self._update_children_checkboxes(item, new_state)
            else:
                self._update_parent_checkbox(item)
        finally:
            self.tree.blockSignals(False)
    
    def _is_group_header(self, item):
        """Checks if the item is a group header."""
        item_text = item.text(0)
        return item_text in ['LandXML', 'Surfaces', 'Alignments', 'CogoPoints']
    
    def _update_children_checkboxes(self, parent_item, state):
        """Updates the checkboxes of child items based on the parent's state."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if child.flags() & Qt.ItemIsUserCheckable:
                child.setCheckState(0, state)
                self._update_children_checkboxes(child, state)
    
    def _update_parent_checkbox(self, item):
        """Updates the parent's checkbox state based on its children's states."""
        parent = item.parent()
        if parent is None or not (parent.flags() & Qt.ItemIsUserCheckable):
            return
        
        checked_count = 0
        total_count = 0
        partially_checked = False
        
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.flags() & Qt.ItemIsUserCheckable:
                total_count += 1
                child_state = child.checkState(0)
                if child_state == Qt.Checked:
                    checked_count += 1
                elif child_state == Qt.PartiallyChecked:
                    partially_checked = True
        
        if checked_count == 0 and not partially_checked:
            parent.setCheckState(0, Qt.Unchecked)
        elif checked_count == total_count and not partially_checked:
            parent.setCheckState(0, Qt.Checked)
        else:
            parent.setCheckState(0, Qt.PartiallyChecked)
        
        self._update_parent_checkbox(parent)
        
    def _collect_checked_items(self, parent_item, items_list):
        """Recursively collects checked items."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if (child.checkState(0) == Qt.Checked and 
                child.data(0, Qt.UserRole) is not None):
                items_list.append(child.data(0, Qt.UserRole))
            self._collect_checked_items(child, items_list)

    def accept(self):
        """
        Accept the task parameters
        """
        if self.errors:

            print('Errors encountered during import:\n')
            for err in self.errors:
                print(err)

        if not self.xml: return

        selected_items = []
        self._collect_checked_items(self.tree.invisibleRootItem(), selected_items)
        
        if not selected_items:
            QMessageBox.warning(self.form, 'Warning', 'Please check at least one item!')
            return
            
        if not self.xml['CgPoints'].get("Groups"):
            geopoints = make_geopoints.create()
            geopoints.Model = self.xml['CgPoints']['All_Points']
        
        for name, ref in self.xml['CgPoints'].get("Groups").items():
            if name not in selected_items: continue
            geopoints = make_geopoints.create(name)

            points = {}
            for name in ref:
                if name in self.xml['CgPoints'].get("All_Points").keys():
                    points[name] = self.xml['CgPoints']['All_Points'][name]
            geopoints.Model = points

        for name, data in self.xml['Surfaces'].items():
            if name not in selected_items: continue

            terrain = make_terrain.create(label=name)
            terrain.Points = data['Points']
            terrain.Faces = data['Faces']

        for name, data in self.xml['Alignments'].items():
            if name not in selected_items: continue
            alignment = make_alignment.create(name)
            alignment.Model = AlignmentModel(data)

        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def needsFullSpace(self):
        return True
