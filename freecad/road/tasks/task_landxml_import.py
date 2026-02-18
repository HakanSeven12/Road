# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the task panel code for the LandXML Importer tool."""

import FreeCAD, FreeCADGui

from .task_panel import TaskPanel
from ..landxml.landxml_reader import LandXMLReader
from ..geometry.alignment.alignment import Alignment
from ..utils.coordinate_system import CoordinateSystem
from ..make import make_terrain, make_alignment, make_geopoints
from ..utils import get_group

from PySide.QtWidgets import (QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTreeWidget, 
                             QTreeWidgetItem, QFileDialog, QMessageBox, QCheckBox)
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
        
        # Coordinate system info label
        self.coord_info_label = QLabel('')
        self.coord_info_label.setWordWrap(True)
        self.coord_info_label.setStyleSheet("QLabel { color: #0066cc; padding: 5px; }")
        main_layout.addWidget(self.coord_info_label)
        
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
            
            # Update coordinate system info
            self._update_coord_system_info()
            
            self.tree.clear()
            self._populate_tree()
            
        except Exception as e:
            self.errors.append(f"Error loading LandXML file: {str(e)}")
            QMessageBox.critical(
                self.form, 
                'Error', 
                f'Failed to load LandXML file:\n{str(e)}'
            )
    
    def _update_coord_system_info(self):
        """Update coordinate system information label."""
        coord_sys_data = self.parsed_data.get('coordinate_system')
        
        if coord_sys_data:
            coord_sys = CoordinateSystem(coord_sys_data)
            
            info_text = "Coordinate System: "
            
            if coord_sys.is_valid():
                epsg_code = coord_sys.get_epsg_code()
                if epsg_code:
                    info_text += f"EPSG:{epsg_code} - "
                info_text += coord_sys.get_name()
                
                if coord_sys.is_projected():
                    info_text += " (Projected)"
                elif coord_sys.is_geographic():
                    info_text += " (Geographic)"
                
                self.coord_info_label.setText(info_text)
            else:
                # Show available info even if CRS couldn't be created
                name = coord_sys_data.get('name', 'Unknown')
                epsg = coord_sys_data.get('epsgCode', 'N/A')
                info_text += f"{name} (EPSG:{epsg}) - Could not create valid CRS"
                self.coord_info_label.setText(info_text)
                self.coord_info_label.setStyleSheet("QLabel { color: #cc6600; padding: 5px; }")
        else:
            self.coord_info_label.setText("No coordinate system information in LandXML file")
            self.coord_info_label.setStyleSheet("QLabel { color: #cc0000; padding: 5px; }")
    
    def _setup_coordinate_system(self):
        """Setup GeoOrigin with coordinate system from LandXML."""
        coord_sys_data = self.parsed_data.get('coordinate_system')
        if not coord_sys_data:
            FreeCAD.Console.PrintWarning(
                "No coordinate system information in LandXML file\n"
            )
            return 
        
        try:
            # Find or create GeoOrigin
            self.geo_origin = get_group.create_project()
            self.geo_origin.Model = CoordinateSystem(coord_sys_data)

            
        except Exception as e:
            FreeCAD.Console.PrintError(
                f"Error setting up GeoOrigin: {str(e)}\n"
            )
            return 
            
    def _populate_tree(self):
        """Populates tree with data from LandXML reader."""
        # Temporarily block signals to prevent premature updates
        self.tree.blockSignals(True)
        
        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, 'LandXML')
        root_item.setText(1, self.parsed_data['filepath'].split('/')[-1])
        root_item.setExpanded(True)
        root_item.setFlags(root_item.flags() | Qt.ItemIsUserCheckable)
        
        # Add alignments
        self._add_alignments_items(root_item)
        
        # Add CgPoints
        self._add_cgpoints_items(root_item)
        
        # Add Surfaces
        self._add_surfaces_items(root_item)
        
        # Now set all checkboxes to Checked after tree is built
        self._check_all_items(root_item)
        
        # Unblock signals
        self.tree.blockSignals(False)
    
    def _check_all_items(self, item):
        """Recursively check all checkable items in the tree."""
        # Check this item if it's checkable
        if item.flags() & Qt.ItemIsUserCheckable:
            item.setCheckState(0, Qt.Checked)
        
        # Recursively check all children
        for i in range(item.childCount()):
            child = item.child(i)
            self._check_all_items(child)
    
    def _add_alignments_items(self, root_item):
        """Adds alignment items to the tree."""
        alignments_data = self.parsed_data.get('alignments', [])
        
        if not alignments_data:
            return
            
        alignments_item = QTreeWidgetItem(root_item)
        alignments_item.setText(0, 'Alignments')
        alignments_item.setText(1, f'({len(alignments_data)} items)')
        alignments_item.setExpanded(True)
        alignments_item.setCheckState(0, Qt.Checked)  # Changed to Checked
        alignments_item.setFlags(alignments_item.flags() | Qt.ItemIsUserCheckable)
        
        for align_data in alignments_data:
            align_name = align_data.get('name', 'Unnamed')
            align_length = align_data.get('length', 0)
            elem_count = len(align_data.get('CoordGeom', []))
            
            align_item = QTreeWidgetItem(alignments_item)
            align_item.setText(0, align_name)
            align_item.setText(1, f'Length: {align_length:.2f}, Elements: {elem_count}')
            align_item.setData(0, Qt.UserRole, {'type': 'alignment', 'data': align_data})
            align_item.setCheckState(0, Qt.Checked)  # Changed to Checked
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
            
            # Add Profile if present
            if 'Profile' in align_data and align_data['Profile']:
                self._add_profile(align_item, align_data['Profile'])
    
    def _add_geometry_elements(self, parent_item, geom_elements):
        """Adds geometry elements as children."""
        if not geom_elements:
            return
        
        geom_group = QTreeWidgetItem(parent_item)
        geom_group.setText(0, 'Geometry')
        geom_group.setText(1, f'({len(geom_elements)} elements)')
        geom_group.setExpanded(False)
        geom_group.setFlags(geom_group.flags() & ~Qt.ItemIsSelectable)
        
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
    
    def _add_profile(self, parent_item, profile_data):
        """Adds profile data as children."""
        profile_name = profile_data.get('name', 'Unnamed Profile')
        
        profile_item = QTreeWidgetItem(parent_item)
        profile_item.setText(0, f'Profile: {profile_name}')
        profile_item.setExpanded(False)
        profile_item.setFlags(profile_item.flags() & ~Qt.ItemIsSelectable)
        
        # Add ProfAlign elements (can be single dict or list)
        if 'ProfAlign' in profile_data:
            profalign_data = profile_data['ProfAlign']
            
            # Handle both single ProfAlign and list of ProfAlign
            if isinstance(profalign_data, dict):
                # Single ProfAlign
                self._add_profalign(profile_item, profalign_data)
            elif isinstance(profalign_data, list):
                # Multiple ProfAlign
                if len(profalign_data) > 1:
                    # Create a group item for multiple profiles
                    profalign_group = QTreeWidgetItem(profile_item)
                    profalign_group.setText(0, 'Design Profiles')
                    profalign_group.setText(1, f'({len(profalign_data)} profiles)')
                    profalign_group.setExpanded(False)
                    profalign_group.setFlags(profalign_group.flags() & ~Qt.ItemIsSelectable)
                    
                    for pa_data in profalign_data:
                        self._add_profalign(profalign_group, pa_data)
                elif len(profalign_data) == 1:
                    # Single ProfAlign in list
                    self._add_profalign(profile_item, profalign_data[0])
        
        # Add ProfSurf elements if present
        if 'ProfSurf' in profile_data:
            self._add_profsurf_list(profile_item, profile_data['ProfSurf'])
    
    def _add_profalign(self, parent_item, profalign_data):
        """Adds vertical alignment (ProfAlign) data."""
        profalign_name = profalign_data.get('name', 'Design Profile')
        geom_elements = profalign_data.get('geometry', [])
        
        profalign_item = QTreeWidgetItem(parent_item)
        profalign_item.setText(0, f'Vertical Alignment: {profalign_name}')
        profalign_item.setText(1, f'({len(geom_elements)} elements)')
        profalign_item.setExpanded(False)
        profalign_item.setFlags(profalign_item.flags() & ~Qt.ItemIsSelectable)
        
    def _add_profsurf_list(self, parent_item, profsurf_list):
        """Adds surface profile (ProfSurf) data."""
        profsurf_group = QTreeWidgetItem(parent_item)
        profsurf_group.setText(0, 'Surface Profiles')
        profsurf_group.setText(1, f'({len(profsurf_list)} surfaces)')
        profsurf_group.setExpanded(False)
        profsurf_group.setFlags(profsurf_group.flags() & ~Qt.ItemIsSelectable)
        
        for profsurf_data in profsurf_list:
            surf_name = profsurf_data.get('name', 'Unnamed Surface')
            points = profsurf_data.get('points', [])
            
            profsurf_item = QTreeWidgetItem(profsurf_group)
            profsurf_item.setText(0, surf_name)
            profsurf_item.setText(1, f'{len(points)} points')
            profsurf_item.setFlags(profsurf_item.flags() & ~Qt.ItemIsSelectable)
    
    def _add_cgpoints_items(self, root_item):
        """Adds CgPoints items to the tree organized by groups."""
        cgpoint_groups = self.parsed_data.get('cgpoint_groups', [])
        
        if not cgpoint_groups:
            return
        
        total_points = sum(len(g.get('points', [])) for g in cgpoint_groups)
        
        cgpoints_item = QTreeWidgetItem(root_item)
        cgpoints_item.setText(0, 'CgPoints')
        cgpoints_item.setText(1, f'({total_points} points in {len(cgpoint_groups)} groups)')
        cgpoints_item.setExpanded(False)
        cgpoints_item.setCheckState(0, Qt.Checked)  # Changed to Checked
        cgpoints_item.setFlags(cgpoints_item.flags() | Qt.ItemIsUserCheckable)
        
        # Add each group
        for group_data in cgpoint_groups:
            group_name = group_data.get('name', 'Unnamed Group')
            points_list = group_data.get('points', [])
            
            if not points_list:
                continue
            
            # Create group item
            group_item = QTreeWidgetItem(cgpoints_item)
            group_item.setText(0, group_name)
            group_item.setText(1, f'({len(points_list)} points)')
            group_item.setExpanded(False)
            group_item.setCheckState(0, Qt.Checked)  # Changed to Checked
            group_item.setFlags(group_item.flags() | Qt.ItemIsUserCheckable)
            group_item.setData(0, Qt.UserRole, {'type': 'cgpoint_group', 'data': group_data})
            
            # Add individual points
            for point_data in points_list:
                self._add_cgpoint_item(group_item, point_data)
    
    def _add_cgpoint_item(self, parent_item, point_data):
        """Adds a single CgPoint item to the tree."""
        point_name = point_data.get('name', 'Unnamed')
        northing = point_data.get('northing', 0)
        easting = point_data.get('easting', 0)
        elevation = point_data.get('elevation', None)
        
        point_item = QTreeWidgetItem(parent_item)
        point_item.setText(0, point_name)
        
        # Format coordinates display
        if elevation is not None:
            coord_str = f'N: {northing:.3f}, E: {easting:.3f}, Z: {elevation:.3f}'
        else:
            coord_str = f'N: {northing:.3f}, E: {easting:.3f}'
        
        point_item.setText(1, coord_str)
        point_item.setData(0, Qt.UserRole, {'type': 'cgpoint', 'data': point_data})
        point_item.setCheckState(0, Qt.Checked)  # Changed to Checked
        point_item.setFlags(point_item.flags() | Qt.ItemIsUserCheckable)
        
        # Add description as child if present
        desc = point_data.get('desc', None)
        if desc:
            desc_item = QTreeWidgetItem(point_item)
            desc_item.setText(0, 'Description')
            desc_item.setText(1, desc)
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsSelectable)
    
    def _add_surfaces_items(self, root_item):
        """Adds surface items to the tree."""
        surfaces_data = self.parsed_data.get('surfaces', [])
        
        if not surfaces_data:
            return
        
        surfaces_item = QTreeWidgetItem(root_item)
        surfaces_item.setText(0, 'Surfaces')
        surfaces_item.setText(1, f'({len(surfaces_data)} surfaces)')
        surfaces_item.setExpanded(False)
        surfaces_item.setCheckState(0, Qt.Checked)  # Changed to Checked
        surfaces_item.setFlags(surfaces_item.flags() | Qt.ItemIsUserCheckable)
        
        for surface_data in surfaces_data:
            surface_name = surface_data.get('name', 'Unnamed')
            surf_type = surface_data.get('surfType', 'Unknown')
            point_count = len(surface_data.get('points', []))
            face_count = len(surface_data.get('faces', []))
            
            surface_item = QTreeWidgetItem(surfaces_item)
            surface_item.setText(0, surface_name)
            surface_item.setText(1, f'Type: {surf_type}, Points: {point_count}, Faces: {face_count}')
            surface_item.setData(0, Qt.UserRole, {'type': 'surface', 'data': surface_data})
            surface_item.setCheckState(0, Qt.Checked)  # Changed to Checked
            surface_item.setFlags(surface_item.flags() | Qt.ItemIsUserCheckable)
            surface_item.setExpanded(False)
            
            # Add surface details as children
            self._add_surface_details(surface_item, surface_data)
    
    def _add_surface_details(self, parent_item, surface_data):
        """Adds surface details as children."""
        # Add description if present
        desc = surface_data.get('desc', None)
        if desc:
            desc_item = QTreeWidgetItem(parent_item)
            desc_item.setText(0, 'Description')
            desc_item.setText(1, desc)
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsSelectable)
        
        # Add elevation range if present
        elev_min = surface_data.get('elevMin')
        elev_max = surface_data.get('elevMax')
        if elev_min is not None and elev_max is not None:
            elev_item = QTreeWidgetItem(parent_item)
            elev_item.setText(0, 'Elevation Range')
            elev_item.setText(1, f'{elev_min:.2f} to {elev_max:.2f}')
            elev_item.setFlags(elev_item.flags() & ~Qt.ItemIsSelectable)
        
        # Add area if present
        area_2d = surface_data.get('area2DSurf')
        area_3d = surface_data.get('area3DSurf')
        if area_2d is not None:
            area_item = QTreeWidgetItem(parent_item)
            area_item.setText(0, '2D Area')
            area_item.setText(1, f'{area_2d:.2f}')
            area_item.setFlags(area_item.flags() & ~Qt.ItemIsSelectable)
        if area_3d is not None:
            area_item = QTreeWidgetItem(parent_item)
            area_item.setText(0, '3D Area')
            area_item.setText(1, f'{area_3d:.2f}')
            area_item.setFlags(area_item.flags() & ~Qt.ItemIsSelectable)
        
        # Add points summary
        points = surface_data.get('points', [])
        if points:
            points_group = QTreeWidgetItem(parent_item)
            points_group.setText(0, 'Points')
            points_group.setText(1, f'({len(points)} points)')
            points_group.setExpanded(False)
            points_group.setFlags(points_group.flags() & ~Qt.ItemIsSelectable)
            
        # Add faces summary
        faces = surface_data.get('faces', [])
        if faces:
            faces_group = QTreeWidgetItem(parent_item)
            faces_group.setText(0, 'Faces')
            faces_group.setText(1, f'({len(faces)} triangles)')
            faces_group.setExpanded(False)
            faces_group.setFlags(faces_group.flags() & ~Qt.ItemIsSelectable)

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
        item_data = item.data(0, Qt.UserRole)
        
        # Check if it's a predefined group or a data group
        if item_text in ['LandXML', 'Surfaces', 'Alignments', 'CgPoints']:
            return True
        
        # Check if it's a CgPoint group
        if item_data and isinstance(item_data, dict):
            if item_data.get('type') == 'cgpoint_group':
                return True
        
        return False
    
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
            item_data = child.data(0, Qt.UserRole)
            
            if (child.checkState(0) == Qt.Checked and 
                item_data is not None and 
                isinstance(item_data, dict) and
                item_data.get('type') == 'alignment'):
                alignments_list.append(item_data['data'])
            
            # Recursively check children
            self._collect_checked_alignment_data(child, alignments_list)
    
    def _collect_checked_cgpoint_data(self, parent_item, cgpoint_groups_list):
        """Recursively collects checked CgPoint group data."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            
            # Check if this is a CgPoint group item
            item_data = child.data(0, Qt.UserRole)
            
            if (child.checkState(0) == Qt.Checked and 
                item_data is not None and 
                isinstance(item_data, dict) and
                item_data.get('type') == 'cgpoint_group'):
                cgpoint_groups_list.append(item_data['data'])
            
            # Recursively check children
            self._collect_checked_cgpoint_data(child, cgpoint_groups_list)
    
    def _collect_checked_surface_data(self, parent_item, surfaces_list):
        """Recursively collects checked Surface data."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            
            # Check if this is a Surface item
            item_data = child.data(0, Qt.UserRole)
            
            if (child.checkState(0) == Qt.Checked and 
                item_data is not None and 
                isinstance(item_data, dict) and
                item_data.get('type') == 'surface'):
                surfaces_list.append(item_data['data'])
            
            # Recursively check children
            self._collect_checked_surface_data(child, surfaces_list)
    
    def _get_next_key(self, model):
        """Get the next available key as a string, finding the first missing number."""
        if not model:
            return "1"
        
        # Extract all numeric values from string keys
        used = set()
        for key in model.keys():
            try:
                # Try to convert string key to integer
                used.add(int(key))
            except (ValueError, TypeError):
                # Skip keys that aren't numeric strings
                pass
        
        if not used:
            return "1"
        
        # Find the first missing number
        max_key = max(used)
        all_numbers = set(range(1, max_key + 1))
        missing = sorted(all_numbers - used)
        
        if missing:
            # Return first missing number as string
            return str(missing[0])
        else:
            # No gaps, return next number as string
            return str(max_key + 1)

    def accept(self):
        """Accept the task parameters and create FreeCAD objects."""
        if self.errors:
            print('Errors encountered during import:\n')
            for err in self.errors:
                print(err)

        if not self.landxml_reader:
            QMessageBox.warning(self.form, 'Warning', 'No LandXML file loaded!')
            return
        
        # Setup GeoOrigin with coordinate system first
        self._setup_coordinate_system()

        # Collect checked alignments
        selected_alignments = []
        self._collect_checked_alignment_data(
            self.tree.invisibleRootItem(), 
            selected_alignments
        )
        
        # Collect checked CgPoint groups
        selected_cgpoint_groups = []
        self._collect_checked_cgpoint_data(
            self.tree.invisibleRootItem(),
            selected_cgpoint_groups
        )
        
        # Collect checked Surfaces
        selected_surfaces = []
        self._collect_checked_surface_data(
            self.tree.invisibleRootItem(),
            selected_surfaces
        )
        
        if not selected_alignments and not selected_cgpoint_groups and not selected_surfaces:
            QMessageBox.warning(
                self.form, 
                'Warning', 
                'Please check at least one item to import!'
            )
            return
        
        # Create alignment objects in FreeCAD
        alignment_created = 0
        alignment_failed = 0
        profile_created = 0
        profile_failed = 0
        
        for align_data in selected_alignments:
            try:
                align_name = align_data.get('name', 'Unnamed Alignment')
                alignment = make_alignment.create(align_name)
                alignment.Model = Alignment(align_data)
                alignment.Model.coordinate_system.set_system('custom', alignment.Model.start_point, swap=True)
                
                print(f"Created alignment: {align_name}")
                alignment_created += 1
                
                # Check if profile was loaded
                if alignment.Model.get_profiles():
                    profile_created += 1
                    profile_name = alignment.Model.profiles.name
                    print(f"  - Profile '{profile_name}' loaded with alignment")
                
            except Exception as e:
                error_msg = f"Failed to create alignment '{align_name}': {str(e)}"
                self.errors.append(error_msg)
                print(error_msg)
                alignment_failed += 1

        # Create CgPoint objects in FreeCAD - one GeoPoints object per group
        cgpoint_created = 0
        cgpoint_failed = 0
        geopoints_created = 0

        if selected_cgpoint_groups:
            for group_data in selected_cgpoint_groups:
                group_name = group_data.get('name', 'Unnamed Group')
                points_list = group_data.get('points', [])
                
                if not points_list:
                    continue
                
                try:
                    # Create a new GeoPoints object with group name
                    geopoints = make_geopoints.create(group_name)
                    
                    # Get the current model (should be empty for new object)
                    model = geopoints.Model.copy()
                    
                    # Add all points in this group to the model
                    for point_data in points_list:
                        key = self._get_next_key(model)
                        
                        model[key] = {
                            "Name": point_data.get('name', 'Unnamed'),
                            "Northing": float(point_data.get('northing', 0)),
                            "Easting": float(point_data.get('easting', 0)),
                            "Elevation": float(point_data.get('elevation', 0)),
                            "Description": point_data.get('desc', '')
                        }
                    
                    # Update the GeoPoints object with the new model
                    geopoints.Model = model
                    
                    cgpoint_created += len(points_list)
                    geopoints_created += 1
                    print(f"Created GeoPoints '{group_name}' with {len(points_list)} points")
                    
                except Exception as e:
                    error_msg = f"Failed to create CgPoints group '{group_name}': {str(e)}"
                    self.errors.append(error_msg)
                    print(error_msg)
                    cgpoint_failed += len(points_list)
        
        # Create Surface objects in FreeCAD as Terrain
        surface_created = 0
        surface_failed = 0
        
        if selected_surfaces:
            for surface_data in selected_surfaces:
                try:
                    surface_name = surface_data.get('name', 'Unnamed Surface')
                    
                    # Get points and faces
                    points = surface_data.get('points', [])
                    faces = surface_data.get('faces', [])
                    
                    if not points or not faces:
                        raise ValueError("Surface has no points or faces")
                    
                    # Create point ID to index mapping
                    point_id_map = {pt['id']: idx for idx, pt in enumerate(points)}
                    
                    # Build Points list for Terrain API
                    # Format: List of (X, Y, Z) tuples where X=Easting, Y=Northing, Z=Elevation
                    terrain_points = []
                    for point in points:
                        easting = point.get('easting', 0)*1000
                        northing = point.get('northing', 0)*1000
                        elevation = point.get('elevation', 0)*1000
                        terrain_points.append((easting, northing, elevation))
                    
                    # Build Faces list for Terrain API
                    # Format: List of (v1, v2, v3) tuples with vertex indices
                    visible_faces = []
                    invisible_faces = []
                    for face in faces:
                        point_ids = face.get('points', [])
                        if len(point_ids) >= 3:
                            # Convert point IDs to vertex indices
                            try:
                                v1 = point_id_map[point_ids[0]]
                                v2 = point_id_map[point_ids[1]]
                                v3 = point_id_map[point_ids[2]]

                                if face.get('invisible'):
                                    invisible_faces.append((v1, v2, v3))
                                else:
                                    visible_faces.append((v1, v2, v3))

                            except KeyError:
                                # Skip faces with missing point references
                                continue
                    
                    # Create Terrain object using the make_terrain API
                    terrain = make_terrain.create(label=surface_name)
                    terrain.Points = terrain_points
                    terrain.Faces = {"Visible":visible_faces, "Invisible":invisible_faces}
                    
                    surface_created += 1
                    print(f"Created terrain '{surface_name}' with {len(visible_faces)} visible faces, {len(invisible_faces)} invisible faces and {len(terrain_points)} points")
                    
                except Exception as e:
                    error_msg = f"Failed to create terrain '{surface_name}': {str(e)}"
                    self.errors.append(error_msg)
                    print(error_msg)
                    surface_failed += 1
        
        # Show summary
        rows = []

        if alignment_created > 0:
            rows.append(f"<tr><td>Alignments created:</td><td align='right'><b>{alignment_created}</b></td></tr>")
        if alignment_failed > 0:
            rows.append(f"<tr><td>Alignments failed:</td><td align='right'><b>{alignment_failed}</b></td></tr>")
        if profile_created > 0:
            rows.append(f"<tr><td>Profiles created:</td><td align='right'><b>{profile_created}</b></td></tr>")
        if profile_failed > 0:
            rows.append(f"<tr><td>Profiles failed:</td><td align='right'><b>{profile_failed}</b></td></tr>")
        if geopoints_created > 0:
            rows.append(f"<tr><td>GeoPoints groups created:</td><td align='right'><b>{geopoints_created}</b></td></tr>")
        if cgpoint_created > 0:
            rows.append(f"<tr><td>Total CgPoints imported:</td><td align='right'><b>{cgpoint_created}</b></td></tr>")
        if cgpoint_failed > 0:
            rows.append(f"<tr><td>CgPoints failed:</td><td align='right'><b>{cgpoint_failed}</b></td></tr>")
        if surface_created > 0:
            rows.append(f"<tr><td>Terrains created:</td><td align='right'><b>{surface_created}</b></td></tr>")
        if surface_failed > 0:
            rows.append(f"<tr><td>Terrains failed:</td><td align='right'><b>{surface_failed}</b></td></tr>")

        table_html = f"""
        <table style='font-size:14px;'>
            {''.join(rows)}
        </table>
        """

        if alignment_created > 0 or cgpoint_created > 0 or surface_created > 0:
            QMessageBox.information(self.form, "Import Complete", table_html)
        else:
            QMessageBox.warning(self.form, "Import Failed", table_html)

        # Close dialog and recompute
        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def needsFullSpace(self):
        return True