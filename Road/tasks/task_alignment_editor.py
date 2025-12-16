# SPDX-License-Identifier: LGPL-2.1-or-later

"""
Task panel for editing alignment using PI (Point of Intersection) method.
Allows adding, editing, and removing PI points to create/update alignment geometry.
"""

import FreeCAD as App
import FreeCADGui as Gui
from PySide2 import QtCore, QtGui, QtWidgets


class AlignmentEditor:
    """
    Task panel for editing alignment geometry using PI points.
    """
    
    def __init__(self, alignment_obj=None):
        """
        Initialize the PI editor panel.
        
        Args:
            alignment_obj: Existing alignment object to edit, or None for new alignment
        """
        self.alignment_obj = alignment_obj
        self.form = self._create_ui()
        self.pi_data = []
        
        # Load existing PI data if editing
        if self.alignment_obj:
            self._load_existing_data()
        else:
            # Add first two default PI points for new alignment
            self._add_default_pis()
    
    def _create_ui(self):
        """Create the UI layout"""
        # Main widget
        widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(widget)
        
        # Title
        title_label = QtWidgets.QLabel("<b>Alignment PI Editor</b>")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Alignment properties group
        props_group = QtWidgets.QGroupBox("Alignment Properties")
        props_layout = QtWidgets.QFormLayout()
        
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("Alignment name")
        if self.alignment_obj:
            self.name_edit.setText(self.alignment_obj.Label)
        props_layout.addRow("Name:", self.name_edit)
        
        self.sta_start_spin = QtWidgets.QDoubleSpinBox()
        self.sta_start_spin.setRange(0, 999999)
        self.sta_start_spin.setDecimals(3)
        self.sta_start_spin.setValue(0.0)
        self.sta_start_spin.setSuffix(" m")
        props_layout.addRow("Start Station:", self.sta_start_spin)
        
        props_group.setLayout(props_layout)
        main_layout.addWidget(props_group)
        
        # PI points table
        pi_group = QtWidgets.QGroupBox("PI Points")
        pi_layout = QtWidgets.QVBoxLayout()
        
        # Table widget
        self.pi_table = QtWidgets.QTableWidget()
        self.pi_table.setColumnCount(6)
        self.pi_table.setHorizontalHeaderLabels([
            "Easting (m)", "Northing (m)", "Radius (m)", 
            "Spiral In (m)", "Spiral Out (m)", "Description"
        ])
        self.pi_table.horizontalHeader().setStretchLastSection(True)
        self.pi_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.pi_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        
        # Set column widths
        self.pi_table.setColumnWidth(0, 100)
        self.pi_table.setColumnWidth(1, 100)
        self.pi_table.setColumnWidth(2, 100)
        self.pi_table.setColumnWidth(3, 100)
        self.pi_table.setColumnWidth(4, 100)
        
        pi_layout.addWidget(self.pi_table)
        
        # Buttons for PI management
        button_layout = QtWidgets.QHBoxLayout()
        
        self.add_pi_btn = QtWidgets.QPushButton("Add PI")
        self.add_pi_btn.setIcon(QtGui.QIcon.fromTheme("list-add"))
        self.add_pi_btn.clicked.connect(self._add_pi_row)
        button_layout.addWidget(self.add_pi_btn)
        
        self.insert_pi_btn = QtWidgets.QPushButton("Insert PI")
        self.insert_pi_btn.setIcon(QtGui.QIcon.fromTheme("insert-object"))
        self.insert_pi_btn.clicked.connect(self._insert_pi_row)
        button_layout.addWidget(self.insert_pi_btn)
        
        self.remove_pi_btn = QtWidgets.QPushButton("Remove PI")
        self.remove_pi_btn.setIcon(QtGui.QIcon.fromTheme("list-remove"))
        self.remove_pi_btn.clicked.connect(self._remove_pi_row)
        button_layout.addWidget(self.remove_pi_btn)
        
        self.move_up_btn = QtWidgets.QPushButton("↑")
        self.move_up_btn.setMaximumWidth(40)
        self.move_up_btn.clicked.connect(self._move_pi_up)
        button_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QtWidgets.QPushButton("↓")
        self.move_down_btn.setMaximumWidth(40)
        self.move_down_btn.clicked.connect(self._move_pi_down)
        button_layout.addWidget(self.move_down_btn)
        
        pi_layout.addLayout(button_layout)
        pi_group.setLayout(pi_layout)
        main_layout.addWidget(pi_group)
        
        # Info label
        self.info_label = QtWidgets.QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("QLabel { color: blue; font-style: italic; }")
        main_layout.addWidget(self.info_label)
        
        # Preview button
        self.preview_btn = QtWidgets.QPushButton("Preview Alignment")
        self.preview_btn.setIcon(QtGui.QIcon.fromTheme("view-refresh"))
        self.preview_btn.clicked.connect(self._preview_alignment)
        main_layout.addWidget(self.preview_btn)
        
        return widget
    
    def _add_default_pis(self):
        """Add two default PI points for new alignment"""
        self._add_pi_row()
        self._add_pi_row()
        
        # Set some default values
        if self.pi_table.rowCount() >= 2:
            self.pi_table.item(0, 0).setText("0.0")
            self.pi_table.item(0, 1).setText("0.0")
            self.pi_table.item(1, 0).setText("100.0")
            self.pi_table.item(1, 1).setText("0.0")
    
    def _load_existing_data(self):
        """Load existing alignment data into the table"""
        if not self.alignment_obj:
            return
        
        try:
            alignment = self.alignment_obj.Model
            
            # Set alignment properties
            if alignment.name:
                self.name_edit.setText(alignment.name)
            self.sta_start_spin.setValue(alignment.sta_start)
            
            # Extract PIs from alignment elements
            pis = alignment.extract_pis_advanced()  # Use advanced extraction
            
            for pi in pis:
                row = self.pi_table.rowCount()
                self.pi_table.insertRow(row)
                
                # Coordinates
                easting, northing = pi['point']
                self.pi_table.setItem(row, 0, QtWidgets.QTableWidgetItem(f"{easting:.3f}"))
                self.pi_table.setItem(row, 1, QtWidgets.QTableWidgetItem(f"{northing:.3f}"))
                
                # Radius
                radius_text = f"{pi['radius']:.3f}" if 'radius' in pi else ""
                self.pi_table.setItem(row, 2, QtWidgets.QTableWidgetItem(radius_text))
                
                # Spirals
                spiral_in_text = f"{pi['spiral_in']:.3f}" if 'spiral_in' in pi else ""
                self.pi_table.setItem(row, 3, QtWidgets.QTableWidgetItem(spiral_in_text))
                
                spiral_out_text = f"{pi['spiral_out']:.3f}" if 'spiral_out' in pi else ""
                self.pi_table.setItem(row, 4, QtWidgets.QTableWidgetItem(spiral_out_text))
                
                # Description
                desc = pi.get('desc', '')
                self.pi_table.setItem(row, 5, QtWidgets.QTableWidgetItem(desc or ""))
            
        except Exception as e:
            App.Console.PrintError(f"Error loading alignment data: {str(e)}\n")
        
    def _add_pi_row(self):
        """Add a new PI point row to the table"""
        row = self.pi_table.rowCount()
        self.pi_table.insertRow(row)
        
        # Add default empty items
        for col in range(6):
            item = QtWidgets.QTableWidgetItem("")
            if col < 5:  # Numeric columns
                item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.pi_table.setItem(row, col, item)
        
        self._update_info()
    
    def _insert_pi_row(self):
        """Insert a new PI row before selected row"""
        current_row = self.pi_table.currentRow()
        if current_row < 0:
            current_row = self.pi_table.rowCount()
        
        self.pi_table.insertRow(current_row)
        
        # Add default empty items
        for col in range(6):
            item = QtWidgets.QTableWidgetItem("")
            if col < 5:  # Numeric columns
                item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.pi_table.setItem(current_row, col, item)
        
        self._update_info()
    
    def _remove_pi_row(self):
        """Remove selected PI row"""
        current_row = self.pi_table.currentRow()
        if current_row >= 0:
            # Prevent removing if less than 2 rows
            if self.pi_table.rowCount() <= 2:
                QtWidgets.QMessageBox.warning(
                    self.form,
                    "Cannot Remove",
                    "Alignment must have at least 2 PI points."
                )
                return
            
            self.pi_table.removeRow(current_row)
            self._update_info()
    
    def _move_pi_up(self):
        """Move selected PI up in the list"""
        current_row = self.pi_table.currentRow()
        if current_row > 0:
            self._swap_rows(current_row, current_row - 1)
            self.pi_table.selectRow(current_row - 1)
    
    def _move_pi_down(self):
        """Move selected PI down in the list"""
        current_row = self.pi_table.currentRow()
        if current_row >= 0 and current_row < self.pi_table.rowCount() - 1:
            self._swap_rows(current_row, current_row + 1)
            self.pi_table.selectRow(current_row + 1)
    
    def _swap_rows(self, row1, row2):
        """Swap two rows in the table"""
        for col in range(self.pi_table.columnCount()):
            item1 = self.pi_table.takeItem(row1, col)
            item2 = self.pi_table.takeItem(row2, col)
            self.pi_table.setItem(row1, col, item2)
            self.pi_table.setItem(row2, col, item1)
    
    def _update_info(self):
        """Update information label"""
        num_pis = self.pi_table.rowCount()
        self.info_label.setText(
            f"Total PI Points: {num_pis}\n"
            f"Note: First and last PI define start and end points (no curve).\n"
            f"Curve parameters apply at middle PI points."
        )
    
    def _get_pi_list(self):
        """Extract PI data from table"""
        pi_list = []
        
        for row in range(self.pi_table.rowCount()):
            try:
                # Get coordinates
                easting_item = self.pi_table.item(row, 0)
                northing_item = self.pi_table.item(row, 1)
                
                if not easting_item or not northing_item:
                    raise ValueError(f"Row {row + 1}: Missing coordinates")
                
                easting_text = easting_item.text().strip()
                northing_text = northing_item.text().strip()
                
                if not easting_text or not northing_text:
                    raise ValueError(f"Row {row + 1}: Empty coordinates")
                
                easting = float(easting_text)
                northing = float(northing_text)
                
                pi = {'point': (easting, northing)}
                
                # Get optional parameters
                radius_item = self.pi_table.item(row, 2)
                if radius_item and radius_item.text().strip():
                    pi['radius'] = float(radius_item.text())
                
                spiral_in_item = self.pi_table.item(row, 3)
                if spiral_in_item and spiral_in_item.text().strip():
                    pi['spiral_in'] = float(spiral_in_item.text())
                
                spiral_out_item = self.pi_table.item(row, 4)
                if spiral_out_item and spiral_out_item.text().strip():
                    pi['spiral_out'] = float(spiral_out_item.text())
                
                desc_item = self.pi_table.item(row, 5)
                if desc_item and desc_item.text().strip():
                    pi['desc'] = desc_item.text()
                
                pi_list.append(pi)
                
            except ValueError as e:
                raise ValueError(f"Invalid data in row {row + 1}: {str(e)}")
        
        return pi_list
    
    def _preview_alignment(self):
        """Preview the alignment with current PI data"""
        try:
            pi_list = self._get_pi_list()
            
            if len(pi_list) < 2:
                QtWidgets.QMessageBox.warning(
                    self.form,
                    "Invalid Data",
                    "At least 2 PI points are required."
                )
                return
            
            # Show preview info
            msg = "Alignment Preview:\n\n"
            msg += f"Number of PIs: {len(pi_list)}\n\n"
            
            for i, pi in enumerate(pi_list):
                msg += f"PI {i + 1}: ({pi['point'][0]:.3f}, {pi['point'][1]:.3f})"
                if 'radius' in pi:
                    msg += f" | R={pi['radius']:.1f}"
                if 'spiral_in' in pi:
                    msg += f" | Ls_in={pi['spiral_in']:.1f}"
                if 'spiral_out' in pi:
                    msg += f" | Ls_out={pi['spiral_out']:.1f}"
                msg += "\n"
            
            QtWidgets.QMessageBox.information(
                self.form,
                "Preview",
                msg
            )
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self.form,
                "Error",
                f"Cannot preview alignment:\n{str(e)}"
            )
    
    def accept(self):
        """Called when OK button is pressed"""
        try:
            # Get alignment name
            name = self.name_edit.text().strip()
            if not name:
                QtWidgets.QMessageBox.warning(
                    self.form,
                    "Invalid Input",
                    "Please enter an alignment name."
                )
                return False
            
            # Get PI data
            pi_list = self._get_pi_list()
            
            if len(pi_list) < 2:
                QtWidgets.QMessageBox.warning(
                    self.form,
                    "Invalid Data",
                    "At least 2 PI points are required."
                )
                return False
            
            # Get start station
            sta_start = self.sta_start_spin.value()
            
            # Create or update alignment
            from ..geometry.alignment.alignment import Alignment
            
            # Update existing alignment
            alignment = Alignment.from_pis(
                pi_list=pi_list,
                name=name,
                sta_start=sta_start
            )
            
            # Update FreeCAD object
            self.alignment_obj.Model = alignment
            self.alignment_obj.Label = name
            
            App.Console.PrintMessage(f"Alignment '{name}' updated successfully.\n")
            return True
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self.form,
                "Error",
                f"Cannot create/update alignment:\n{str(e)}"
            )
            App.Console.PrintError(f"Alignment creation error: {str(e)}\n")
            return False
    
    def reject(self):
        """Called when Cancel button is pressed"""
        return True