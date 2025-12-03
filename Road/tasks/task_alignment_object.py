# SPDX-License-Identifier: LGPL-2.1-or-later
"""Task panel for creating Alignment from 2D object."""

import FreeCAD
import FreeCADGui

from PySide.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QGroupBox, QFormLayout, QLineEdit, 
                             QDoubleSpinBox, QCheckBox, QPushButton,
                             QLabel, QMessageBox)

from .task_panel import TaskPanel
from ..make import make_alignment
from ..geometry.alignment import Alignment
from ..functions.alignment_data_from_object import extract_alignment_data


class TaskAlignmentObject(TaskPanel):
    """Task panel for alignment creation from 2D object"""
    
    def __init__(self, source_obj):
        """
        Initialize task panel.
        
        Args:
            source_obj: FreeCAD object to convert to alignment
        """
        self.source_obj = source_obj
        
        # Create widget
        widget = QWidget()
        self.setup_ui(widget)
        
        # Initialize parent with widget
        super().__init__(widget)
    
    def setup_ui(self, widget):
        """Setup dialog UI"""
        layout = QVBoxLayout()
        
        # Source object info
        info_group = QGroupBox("Source Object")
        info_layout = QFormLayout()
        
        self.obj_label = QLabel(self.source_obj.Label)
        info_layout.addRow("Object:", self.obj_label)
        
        # Get shape statistics
        edge_count = len(self.source_obj.Shape.Edges)
        self.edge_count_label = QLabel(str(edge_count))
        info_layout.addRow("Edges:", self.edge_count_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Alignment parameters
        params_group = QGroupBox("Alignment Parameters")
        params_layout = QFormLayout()
        
        # Alignment name
        self.name_edit = QLineEdit()
        self.name_edit.setText(f"{self.source_obj.Label}_Alignment")
        params_layout.addRow("Name:", self.name_edit)
        
        # Start station
        self.start_sta_spin = QDoubleSpinBox()
        self.start_sta_spin.setRange(-1e9, 1e9)
        self.start_sta_spin.setValue(0.0)
        self.start_sta_spin.setDecimals(3)
        self.start_sta_spin.setSingleStep(10.0)
        params_layout.addRow("Start Station:", self.start_sta_spin)
        
        # Description
        self.desc_edit = QLineEdit()
        self.desc_edit.setText(f"Created from {self.source_obj.Label}")
        params_layout.addRow("Description:", self.desc_edit)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.reverse_check = QCheckBox("Reverse Direction")
        options_layout.addWidget(self.reverse_check)
        
        self.delete_source_check = QCheckBox("Delete Source Object")
        options_layout.addWidget(self.delete_source_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        layout.addStretch()
        widget.setLayout(layout)
    
    def accept(self):
        """Accept button callback - create alignment"""
        try:
            # Get parameters
            name = self.name_edit.text()
            description = self.desc_edit.text()
            start_sta = self.start_sta_spin.value()
            reverse = self.reverse_check.isChecked()
            
            # Extract geometry data using helper function from command module
            alignment_data = extract_alignment_data(
                self.source_obj,
                name,
                description,
                start_sta,
                reverse
            )
            
            if alignment_data is None:
                FreeCAD.Console.PrintError("Failed to extract alignment data.\n")
                return False
            
            # Create alignment object
            alignment = make_alignment.create(alignment_data.get('name', 'Alignment'))
            alignment.Model = Alignment(alignment_data)
            alignment.Model.coordinate_system.set_system('custom', alignment.Model.start_point, swap=True)
            
            if alignment is None:
                FreeCAD.Console.PrintError("Failed to create alignment.\n")
                return False
            
            # Delete source object if requested
            if self.delete_source_check.isChecked():
                FreeCAD.ActiveDocument.removeObject(self.source_obj.Name)
            
            FreeCAD.ActiveDocument.recompute()
            
            FreeCAD.Console.PrintMessage(
                f"Alignment '{name}' created successfully.\n"
            )
            
            FreeCADGui.Control.closeDialog()
            return True
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error creating alignment: {str(e)}\n")
            QMessageBox.critical(
                None,
                "Error",
                f"Failed to create alignment:\n{str(e)}"
            )
            return False
    
    def needsFullSpace(self):
        """Return True if task panel needs full space"""
        return False