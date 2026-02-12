# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the task panel code for the Cluster Importer tool."""

import FreeCAD, FreeCADGui
from PySide import QtCore, QtWidgets
import csv, os

from .task_panel import TaskPanel
from ..utils import get_group
from ..make import make_geopoints


class TaskGeoPointsImport(TaskPanel):
    """Command to import point file which includes survey data."""
    def __init__(self):
        # Create UI programmatically
        self.form = self._create_ui()
        self.setup_connections()
        self.load_clusters()
    
    def _create_ui(self):
        """Create the UI programmatically without external .ui file."""
        # Main widget
        widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(widget)
        
        # Top section with file selection and column configuration side by side
        top_layout = QtWidgets.QHBoxLayout()
        
        # File selection group
        file_group = QtWidgets.QGroupBox("File Selection")
        file_layout = QtWidgets.QVBoxLayout()
        
        file_buttons_layout = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QPushButton("Add Files")
        self.remove_button = QtWidgets.QPushButton("Remove Files")
        file_buttons_layout.addWidget(self.add_button)
        file_buttons_layout.addWidget(self.remove_button)
        
        self.selected_files_list = QtWidgets.QListWidget()
        self.selected_files_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
        file_layout.addWidget(self.selected_files_list)
        file_layout.addLayout(file_buttons_layout)
        file_group.setLayout(file_layout)
        
        # Column configuration group
        column_group = QtWidgets.QGroupBox("Column Mapping")
        column_layout = QtWidgets.QVBoxLayout()
        
        # Column numbers section (form layout)
        form_layout = QtWidgets.QFormLayout()
        
        self.point_name_edit = QtWidgets.QLineEdit("1")
        self.easting_edit = QtWidgets.QLineEdit("2")
        self.northing_edit = QtWidgets.QLineEdit("3")
        self.elevation_edit = QtWidgets.QLineEdit("4")
        self.description_edit = QtWidgets.QLineEdit("5")
        
        form_layout.addRow("Name:", self.point_name_edit)
        form_layout.addRow("Easting:", self.easting_edit)
        form_layout.addRow("Northing:", self.northing_edit)
        form_layout.addRow("Elevation:", self.elevation_edit)
        form_layout.addRow("Description:", self.description_edit)
        
        column_layout.addLayout(form_layout)
        column_group.setLayout(column_layout)
        
        # Delimiter section (vertical layout)
        delimiter_label = QtWidgets.QLabel("Delimiter:")
        self.delimiter_combo = QtWidgets.QComboBox()
        self.delimiter_combo.addItems(["White Space", "Comma", "Tab"])
        column_layout.addWidget(delimiter_label)
        column_layout.addWidget(self.delimiter_combo)
        
        # Add both groups to top layout
        top_layout.addWidget(file_group)
        top_layout.addWidget(column_group)
        
        # Point group configuration
        group_widget = QtWidgets.QWidget()
        group_layout = QtWidgets.QHBoxLayout(group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        
        self.point_group_checkbox = QtWidgets.QCheckBox("Add to Point Group")
        self.subgroup_combo = QtWidgets.QComboBox()
        self.subgroup_combo.setEnabled(False)
        self.create_group_button = QtWidgets.QPushButton("Create New Group")
        self.create_group_button.setEnabled(False)
        
        group_layout.addWidget(self.point_group_checkbox)
        group_layout.addWidget(self.subgroup_combo)
        group_layout.addWidget(self.create_group_button)
        group_layout.addStretch()
        
        # Preview group
        preview_group = QtWidgets.QGroupBox("Preview")
        preview_layout = QtWidgets.QVBoxLayout()
        
        self.preview_label = QtWidgets.QLabel("No file selected")
        self.preview_table = QtWidgets.QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(
            ["Name", "Easting", "Northing", "Elevation", "Description"]
        )
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        
        # Hide row numbers
        self.preview_table.verticalHeader().setVisible(False)
        
        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview_table)
        preview_group.setLayout(preview_layout)
        
        # Add all sections to main layout
        main_layout.addLayout(top_layout)
        main_layout.addWidget(group_widget)
        main_layout.addWidget(preview_group)
        
        return widget

    def setup_connections(self):
        """Connect UI elements to their respective functions."""
        self.add_button.clicked.connect(self.add_file)
        self.remove_button.clicked.connect(self.remove_file)
        self.selected_files_list.itemSelectionChanged.connect(self.preview)
        self.point_group_checkbox.stateChanged.connect(self.toggle_cluster_selection)
        self.create_group_button.clicked.connect(self.show_cluster_creation_ui)
        
        # Add connections for column number changes
        self.point_name_edit.textChanged.connect(self.preview)
        self.northing_edit.textChanged.connect(self.preview)
        self.easting_edit.textChanged.connect(self.preview)
        self.elevation_edit.textChanged.connect(self.preview)
        self.description_edit.textChanged.connect(self.preview)
        self.delimiter_combo.currentTextChanged.connect(self.preview)
        
    def load_clusters(self):
        """Load clusters into the combo box."""
        clusters = get_group.get("Clusters")
        self.group_dict = {
            cluster.Label: cluster for cluster in clusters.Group if cluster.Proxy.Type == 'Road::GeoPoints'
        }
        self.subgroup_combo.addItems(self.group_dict.keys())

    def add_file(self):
        """Add selected files to the list widget."""
        path = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/General").GetString("FileOpenSavePath")
        file_names, _ = QtWidgets.QFileDialog.getOpenFileNames(None, "Select files", path, 'All Files (*.*)')
        
        for file_path in file_names:
            item = QtWidgets.QListWidgetItem(os.path.basename(file_path))
            item.setData(QtCore.Qt.UserRole, file_path)  # Store full path in item data
            self.selected_files_list.addItem(item)

    def remove_file(self):
        """Remove selected files from the list widget."""
        for item in self.selected_files_list.selectedItems():
            self.selected_files_list.takeItem(self.selected_files_list.row(item))

    def toggle_cluster_selection(self):
        """Toggle the cluster selection UI elements."""
        enabled = self.point_group_checkbox.isChecked()
        self.subgroup_combo.setEnabled(enabled)
        self.create_group_button.setEnabled(enabled)

    def show_cluster_creation_ui(self):
        """Display the cluster creation subpanel."""
        dialog = QtWidgets.QDialog(self.form)
        dialog.setWindowTitle("Create Point Group")
        dialog_layout = QtWidgets.QVBoxLayout(dialog)
        
        # Group name input
        form_layout = QtWidgets.QFormLayout()
        group_name_edit = QtWidgets.QLineEdit()
        form_layout.addRow("Point Group Name:", group_name_edit)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        ok_button = QtWidgets.QPushButton("OK")
        cancel_button = QtWidgets.QPushButton("Cancel")
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        dialog_layout.addLayout(form_layout)
        dialog_layout.addLayout(button_layout)
        
        # Connect buttons
        ok_button.clicked.connect(lambda: self.create_cluster(group_name_edit.text(), dialog))
        cancel_button.clicked.connect(dialog.close)
        
        dialog.exec_()

    def create_cluster(self, group_name, dialog):
        """Create a new cluster and add it to the combo box."""
        if not group_name:
            return
        new_group = make_geopoints.create(group_name)
        self.group_dict[new_group.Label] = new_group
        self.subgroup_combo.addItem(new_group.Label)
        dialog.close()

    def file_reader(self, file, operation):
        """Read and process file content for preview or import."""
        delimiters = {"White Space": ' ', "Comma": ',', "Tab": '\t'}
        delimiter = delimiters.get(self.delimiter_combo.currentText(), ' ')
        reader = csv.reader(file, delimiter=delimiter, skipinitialspace=True)

        name = int(text) - 1 if (text := self.point_name_edit.text()).isdigit() else None
        northing = int(text) - 1 if (text := self.northing_edit.text()).isdigit() else None
        easting = int(text) - 1 if (text := self.easting_edit.text()).isdigit() else None
        elevation = int(text) - 1 if (text := self.elevation_edit.text()).isdigit() else None
        description = int(text) - 1 if (text := self.description_edit.text()).isdigit() else None

        indices = [name, easting, northing, elevation, description]

        if operation == "Preview":
            self.preview_data(reader, indices)
        elif operation == "Import":
            self.import_data(reader, indices)
            
    def preview_data(self, reader, indices):
        """Fill the preview table with file data."""
        self.preview_table.setRowCount(0)
        for row in reader:
            num_rows = self.preview_table.rowCount()
            self.preview_table.insertRow(num_rows)
            for col, index in enumerate(indices):
                if index is None: continue
                if index < len(row):
                    self.preview_table.setItem(num_rows, col, QtWidgets.QTableWidgetItem(row[index]))
        
        # Resize columns to fit content
        self.preview_table.resizeColumnsToContents()
        
    def import_data(self, reader, indices):
        """Import data from the file into the selected cluster."""
        cluster = self.get_selected_group()
        model = cluster.Model.copy()
        for row in reader:
            key = self.get_key(model)
            model[key] = {
                "Name": row[indices[0]] if indices[0] is not None and indices[0] < len(row) else "GeoPoint", 
                "Easting": float(row[indices[1]]) if indices[1] is not None and indices[1] < len(row) else 0.0, 
                "Northing": float(row[indices[2]]) if indices[2] is not None and indices[2] < len(row) else 0.0, 
                "Elevation": float(row[indices[3]]) if indices[3] is not None and indices[3] < len(row) else 0.0, 
                "Description": row[indices[4]] if indices[4] is not None and indices[4] < len(row) else ""}
            
        cluster.Model = model

    def get_key(self, model):
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

    def preview(self):
        """Preview the selected file."""
        selected_file = self.selected_files_list.selectedItems()
        if selected_file:
            file_path = selected_file[0].data(QtCore.Qt.UserRole)  # Get full path from item data
            file_name = os.path.basename(file_path)
            
            # Shorten file name if too long (keep beginning and end visible)
            max_length = 40
            if len(file_name) > max_length:
                # Calculate how many characters to keep from start and end
                side_length = (max_length - 3) // 2  # 3 for "..."
                display_name = file_name[:side_length] + "..." + file_name[-side_length:]
            else:
                display_name = file_name
            
            self.preview_label.setText(f"Preview: {display_name}")
            with open(file_path, 'r') as file:
                self.file_reader(file, "Preview")

    def get_selected_group(self):
        """Get the currently selected cluster."""
        if self.point_group_checkbox.isChecked():
            return self.group_dict.get(self.subgroup_combo.currentText())
        return make_geopoints.create()

    def accept(self):
        """Accept and process the selected files for import."""
        if self.selected_files_list.count() == 0:
            FreeCAD.Console.PrintMessage("No Files selected\n")
            return

        for i in range(self.selected_files_list.count()):
            file_path = self.selected_files_list.item(i).data(QtCore.Qt.UserRole)  # Get full path from item data
            with open(file_path, 'r') as file:
                self.file_reader(file, "Import")

        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def needsFullSpace(self):
        return True