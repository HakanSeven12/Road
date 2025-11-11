# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the task panel code for the LandXML Importer tool."""

import FreeCAD, FreeCADGui

from .task_panel import TaskPanel
from ..functions.landxml_reader import LandXMLReader
from ..geometry.alignment import Alignment
from ..make import make_terrain, make_alignment, make_geopoints

from PySide.QtWidgets import (QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTreeWidget, 
                             QTreeWidgetItem, QFileDialog, QMessageBox)
from PySide.QtCore import Qt


class TaskLandXMLImport(TaskPanel):
    def __init__(self):
        super().__init__()
        self.form = QWidget()
        self.landxml_reader = None
        self.selected_file = None
        self.parsed_data = {}
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
        self.tree.setHeaderLabels(['Item', 'Details'])
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
        try:
            self.landxml_reader = LandXMLReader(file_path)
            self.parsed_data = self.landxml_reader.export_to_dict()
            
            self.tree.clear()
            self._populate_tree()
            
        except Exception as e:
            self.errors.append(f"Error loading LandXML file: {str(e)}")
            QMessageBox.critical(
                self.form, 
                'Error', 
                f'Failed to load LandXML file:\n{str(e)}'
            )
            
    def _populate_tree(self):
        """Populates tree with data from LandXML reader."""
        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, 'LandXML')
        root_item.setText(1, self.parsed_data['filepath'].split('/')[-1])
        root_item.setExpanded(True)
        root_item.setCheckState(0, Qt.Unchecked)
        root_item.setFlags(root_item.flags() | Qt.ItemIsUserCheckable)
        
        # Add alignments
        self._add_alignments_items(root_item)
        
        # TODO: Add surfaces and cogo points when parser supports them
        # self._add_surfaces_items(root_item)
        # self._add_cogo_points_items(root_item)
        
    def _add_alignments_items(self, root_item):
        """Adds alignment items to the tree."""
        alignments_data = self.parsed_data.get('alignments', [])
        
        if not alignments_data:
            return
            
        alignments_item = QTreeWidgetItem(root_item)
        alignments_item.setText(0, 'Alignments')
        alignments_item.setText(1, f'({len(alignments_data)} items)')
        alignments_item.setExpanded(True)
        alignments_item.setCheckState(0, Qt.Unchecked)
        alignments_item.setFlags(alignments_item.flags() | Qt.ItemIsUserCheckable)
        
        for align_data in alignments_data:
            align_name = align_data.get('name', 'Unnamed')
            align_length = align_data.get('length', 0)
            elem_count = len(align_data.get('CoordGeom', []))
            
            align_item = QTreeWidgetItem(alignments_item)
            align_item.setText(0, align_name)
            align_item.setText(1, f'Length: {align_length:.2f}, Elements: {elem_count}')
            align_item.setData(0, Qt.UserRole, align_data)  # Store full data
            align_item.setCheckState(0, Qt.Unchecked)
            align_item.setFlags(align_item.flags() | Qt.ItemIsUserCheckable)
            align_item.setExpanded(False)
            
            # Add geometry elements as children
            self._add_geometry_elements(align_item, align_data.get('CoordGeom', []))
            
            # Add station equations if present
            if 'StaEquation' in align_data and align_data['StaEquation']:
                self._add_station_equations(align_item, align_data['StaEquation'])
            
            # Add PI points if present
            if 'AlignPIs' in align_data and align_data['AlignPIs']:
                self._add_pi_points(align_item, align_data['AlignPIs'])
    
    def _add_geometry_elements(self, parent_item, geom_elements):
        """Adds geometry elements as children."""
        if not geom_elements:
            return
        
        geom_group = QTreeWidgetItem(parent_item)
        geom_group.setText(0, 'Geometry')
        geom_group.setText(1, f'({len(geom_elements)} elements)')
        geom_group.setExpanded(False)
        geom_group.setFlags(geom_group.flags() & ~Qt.ItemIsSelectable)
        
        for i, geom in enumerate(geom_elements):
            geom_type = geom.get('Type', 'Unknown')
            geom_length = geom.get('length', geom.get('Length', 0))
            
            geom_item = QTreeWidgetItem(geom_group)
            geom_item.setText(0, f'{i+1}. {geom_type}')
            geom_item.setText(1, f'Length: {geom_length:.2f}')
            geom_item.setFlags(geom_item.flags() & ~Qt.ItemIsSelectable)
            
            # Add specific attributes based on type
            if geom_type == 'Curve':
                radius = geom.get('radius', 0)
                delta = geom.get('delta', 0)
                geom_item.setText(1, f'R={radius:.2f}, Δ={delta:.4f} rad')
            elif geom_type == 'Spiral':
                r_start = geom.get('StartRadius', float('inf'))
                r_end = geom.get('EndRadius', float('inf'))
                r_start_str = 'INF' if r_start == float('inf') else f'{r_start:.2f}'
                r_end_str = 'INF' if r_end == float('inf') else f'{r_end:.2f}'
                geom_item.setText(1, f'Rs={r_start_str}, Re={r_end_str}, L={geom_length:.2f}')
    
    def _add_station_equations(self, parent_item, equations):
        """Adds station equations as children."""
        eq_group = QTreeWidgetItem(parent_item)
        eq_group.setText(0, 'Station Equations')
        eq_group.setText(1, f'({len(equations)} equations)')
        eq_group.setExpanded(False)
        eq_group.setFlags(eq_group.flags() & ~Qt.ItemIsSelectable)
        
        for i, eq in enumerate(equations):
            sta_back = eq.get('staBack', 0)
            sta_ahead = eq.get('staAhead', 0)
            adjustment = sta_ahead - sta_back
            
            eq_item = QTreeWidgetItem(eq_group)
            eq_item.setText(0, f'{i+1}. {sta_back:.2f} = {sta_ahead:.2f}')
            eq_item.setText(1, f'Adjustment: {adjustment:+.2f}')
            eq_item.setFlags(eq_item.flags() & ~Qt.ItemIsSelectable)
    
    def _add_pi_points(self, parent_item, pi_points):
        """Adds PI points as children."""
        pi_group = QTreeWidgetItem(parent_item)
        pi_group.setText(0, 'PI Points')
        pi_group.setText(1, f'({len(pi_points)} points)')
        pi_group.setExpanded(False)
        pi_group.setFlags(pi_group.flags() & ~Qt.ItemIsSelectable)
        
        for i, pi in enumerate(pi_points):
            point = pi.get('point', (0, 0))
            station = pi.get('station', None)
            
            pi_item = QTreeWidgetItem(pi_group)
            pi_item.setText(0, f'{i+1}. PI')
            
            if station is not None:
                pi_item.setText(1, f'Sta: {station:.2f}, ({point[0]:.2f}, {point[1]:.2f})')
            else:
                pi_item.setText(1, f'({point[0]:.2f}, {point[1]:.2f})')
            
            pi_item.setFlags(pi_item.flags() & ~Qt.ItemIsSelectable)
    
    def _add_cogo_points_items(self, root_item):
        """Adds CogoPoints items to the tree. (TODO: Implement when parser supports it)"""
        # TODO: Implement CogoPoints parsing in LandXMLReader
        pass
    
    def _add_surfaces_items(self, root_item):
        """Adds surface items to the tree. (TODO: Implement when parser supports it)"""
        # TODO: Implement Surfaces parsing in LandXMLReader
        pass

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
        
    def _collect_checked_alignment_data(self, parent_item, alignments_list):
        """Recursively collects checked alignment data."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            
            # Check if this is an alignment item (has data stored)
            align_data = child.data(0, Qt.UserRole)
            
            if (child.checkState(0) == Qt.Checked and 
                align_data is not None and 
                isinstance(align_data, dict) and
                'CoordGeom' in align_data):
                alignments_list.append(align_data)
            
            # Recursively check children
            self._collect_checked_alignment_data(child, alignments_list)

    def accept(self):
        """Accept the task parameters and create FreeCAD objects."""
        if self.errors:
            print('Errors encountered during import:\n')
            for err in self.errors:
                print(err)

        if not self.landxml_reader:
            QMessageBox.warning(self.form, 'Warning', 'No LandXML file loaded!')
            return

        # Collect checked alignments
        selected_alignments = []
        self._collect_checked_alignment_data(
            self.tree.invisibleRootItem(), 
            selected_alignments
        )
        
        if not selected_alignments:
            QMessageBox.warning(
                self.form, 
                'Warning', 
                'Please check at least one alignment to import!'
            )
            return
        
        # Create alignment objects in FreeCAD
        created_count = 0
        failed_count = 0
        
        for align_data in selected_alignments:
            try:
                align_name = align_data.get('name', 'Unnamed Alignment')
                alignment = make_alignment.create(align_name)
                alignment.Model = Alignment(align_data)
                
                print(f"Created alignment: {align_name}")
                created_count += 1
                
            except Exception as e:
                error_msg = f"Failed to create alignment '{align_name}': {str(e)}"
                self.errors.append(error_msg)
                print(error_msg)
                failed_count += 1
        
        # Show summary
        summary_msg = f"Import completed:\n"
        summary_msg += f"  Created: {created_count} alignment(s)\n"
        if failed_count > 0:
            summary_msg += f"  Failed: {failed_count} alignment(s)\n"
        
        if created_count > 0:
            QMessageBox.information(self.form, 'Import Complete', summary_msg)
        else:
            QMessageBox.warning(self.form, 'Import Failed', summary_msg)
        
        # Close dialog and recompute
        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()

    def needsFullSpace(self):
        return True