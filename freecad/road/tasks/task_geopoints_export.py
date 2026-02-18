# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the task panel code for the Cluster Exporter tool."""

import FreeCAD, FreeCADGui
from PySide import QtCore, QtWidgets

from .task_panel import TaskPanel
from ..utils import get_group


class TaskGeoPointsExport(TaskPanel):
    """Command to export point groups to file."""
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
        
        # Top section with point groups and column configuration side by side
        top_layout = QtWidgets.QHBoxLayout()
        
        # Point groups selection
        groups_group = QtWidgets.QGroupBox("Point Groups")
        groups_layout = QtWidgets.QVBoxLayout()
        
        self.point_groups_list = QtWidgets.QListWidget()
        # Enable checkboxes for items
        self.point_groups_list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        
        groups_layout.addWidget(self.point_groups_list)
        groups_group.setLayout(groups_layout)
        
        # Column configuration group
        column_group = QtWidgets.QGroupBox("Column Mapping")
        column_layout = QtWidgets.QVBoxLayout()
        
        # Delimiter section (vertical layout)
        delimiter_label = QtWidgets.QLabel("Delimiter:")
        self.delimiter_combo = QtWidgets.QComboBox()
        self.delimiter_combo.addItems(["White Space", "Comma"])
        column_layout.addWidget(delimiter_label)
        column_layout.addWidget(self.delimiter_combo)
        
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
        
        # Add both groups to top layout
        top_layout.addWidget(groups_group)
        top_layout.addWidget(column_group)
        
        # File destination section
        destination_group = QtWidgets.QGroupBox("Export Destination")
        destination_layout = QtWidgets.QHBoxLayout()
        
        self.file_destination_edit = QtWidgets.QLineEdit()
        self.file_destination_edit.setPlaceholderText("Select export file location...")
        self.browse_button = QtWidgets.QPushButton("Browse...")
        
        destination_layout.addWidget(self.file_destination_edit)
        destination_layout.addWidget(self.browse_button)
        destination_group.setLayout(destination_layout)
        
        # Add all sections to main layout
        main_layout.addLayout(top_layout)
        main_layout.addWidget(destination_group)
        
        return widget
    
    def setup_connections(self):
        """Connect UI elements to their respective functions."""
        self.browse_button.clicked.connect(self.file_destination)
        self.point_groups_list.itemClicked.connect(self.toggle_checkbox)
    
    def load_clusters(self):
        """Load point groups into the list widget."""
        clusters = get_group.get("Clusters")
        self.group_dict = {
            child.Label: child for child in clusters.Group if child.Proxy.Type == "Road::GeoPoints"
        }
        
        # Add items with checkboxes
        for label in self.group_dict.keys():
            item = QtWidgets.QListWidgetItem(label)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.point_groups_list.addItem(item)

    def file_destination(self):
        """Get file destination."""
        # Select file
        parameter = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/General")
        path = parameter.GetString("FileOpenSavePath")
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
            None, "Save File", path, "Text Files (*.txt);;All Files (*)")

        if file_name:
            self.file_destination_edit.setText(
                file_name if file_name.endswith(".txt") else file_name + ".txt")
    
    def toggle_checkbox(self, item):
        """Toggle checkbox when item is clicked."""
        if item.checkState() == QtCore.Qt.Checked:
            item.setCheckState(QtCore.Qt.Unchecked)
        else:
            item.setCheckState(QtCore.Qt.Checked)

    def accept(self):
        """Export selected point group(s)."""
        # Get user inputs
        if not self.file_destination_edit.text().strip() or self.point_groups_list.count() < 1:
            FreeCAD.Console.PrintError("No file destination or point groups found!\n")
            return
        
        # Get checked items
        checked_items = []
        for i in range(self.point_groups_list.count()):
            item = self.point_groups_list.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                checked_items.append(item.text())
        
        if not checked_items:
            FreeCAD.Console.PrintError("No point groups selected!\n")
            return

        # Set delimiter
        delimiter_map = {"White Space": ' ', "Comma": ','}
        delimiter = delimiter_map.get(self.delimiter_combo.currentText(), ' ')

        # Retrieve index inputs from user
        try:
            indexes = [
                int(self.point_name_edit.text()) - 1,
                int(self.easting_edit.text()) - 1,
                int(self.northing_edit.text()) - 1,
                int(self.elevation_edit.text()) - 1,
                int(self.description_edit.text()) - 1]

        except ValueError:
            FreeCAD.Console.PrintError("Please enter valid integer indices.\n")
            return

        try:
            with open(self.file_destination_edit.text(), 'w') as file:
                # Get checked point groups
                for group_name in checked_items:
                    cluster = self.group_dict[group_name]

                    # Print points to the file
                    for number, point in cluster.Model.items():
                        # Create data list based on geopoint attributes
                        datas = [
                            point['Name'],               # PointName
                            f"{point['Easting']:.3f}",   # Easting
                            f"{point['Northing']:.3f}",  # Northing
                            f"{point['Elevation']:.3f}", # Elevation
                            point['Description'] or ""]  # Description

                        # Write data based on user-specified indexes
                        ordered_data = [None] * 5
                        for data, index in zip(datas, indexes):
                            ordered_data[index] = data

                        file.write(delimiter.join(ordered_data) + "\n")
            FreeCADGui.Control.closeDialog()

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error opening file: {e}\n")
    
    def needsFullSpace(self):
        return False