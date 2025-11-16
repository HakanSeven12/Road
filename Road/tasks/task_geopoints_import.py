# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the task panel code for the Cluster Importer tool."""

import FreeCAD, FreeCADGui
from PySide import QtCore, QtWidgets
import csv, os

from ..variables import ui_path
from .task_panel import TaskPanel
from ..utils import get_group
from ..make import make_geopoints


class TaskGeoPointsImport(TaskPanel):
    """Command to import point file which includes survey data."""
    def __init__(self):
        # Load UI and setup initial connections
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(ui_path, "import_points.ui"))
        self.setup_connections()
        self.load_clusters()

    def setup_connections(self):
        """Connect UI elements to their respective functions."""
        self.form.AddB.clicked.connect(self.add_file)
        self.form.RemoveB.clicked.connect(self.remove_file)
        self.form.SelectedFilesLW.itemSelectionChanged.connect(self.preview)
        self.form.PointGroupChB.stateChanged.connect(self.toggle_cluster_selection)
        self.form.CreateGroupB.clicked.connect(self.show_cluster_creation_ui)

    def load_clusters(self):
        """Load clusters into the combo box."""
        clusters = get_group.get("Clusters")
        self.group_dict = {
            cluster.Label: cluster for cluster in clusters.Group if cluster.Proxy.Type == 'Road::GeoPoints'
        }
        self.form.SubGroupListCB.addItems(self.group_dict.keys())

    def add_file(self):
        """Add selected files to the list widget."""
        path = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/General").GetString("FileOpenSavePath")
        file_names, _ = QtWidgets.QFileDialog.getOpenFileNames(None, "Select files", path, 'All Files (*.*)')
        self.form.SelectedFilesLW.addItems(file_names)

    def remove_file(self):
        """Remove selected files from the list widget."""
        for item in self.form.SelectedFilesLW.selectedItems():
            self.form.SelectedFilesLW.takeItem(self.form.SelectedFilesLW.row(item))

    def toggle_cluster_selection(self):
        """Toggle the cluster selection UI elements."""
        enabled = self.form.PointGroupChB.isChecked()
        self.form.SubGroupListCB.setEnabled(enabled)
        self.form.CreateGroupB.setEnabled(enabled)

    def show_cluster_creation_ui(self):
        """Display the cluster creation subpanel."""
        subpanel = FreeCADGui.PySideUic.loadUi(os.path.join(ui_path, "create_pg.ui"))
        subpanel.setParent(self.form)
        subpanel.setWindowFlags(QtCore.Qt.Window)
        subpanel.show()
        self.subpanel = subpanel
        subpanel.OkB.clicked.connect(self.create_cluster)
        subpanel.CancelB.clicked.connect(subpanel.close)

    def create_cluster(self):
        """Create a new cluster and add it to the combo box."""
        group_name = self.subpanel.PointGroupNameLE.text()
        new_group = make_geopoints.create(group_name)
        self.group_dict[new_group.Label] = new_group
        self.form.SubGroupListCB.addItem(new_group.Label)
        self.subpanel.close()

    def file_reader(self, file, operation):
        """Read and process file content for preview or import."""
        delimiters = {"White Space": ' ', "Comma": ',', "Tab": '\t'}
        delimiter = delimiters.get(self.form.DelimiterCB.currentText(), ' ')
        reader = csv.reader(file, delimiter=delimiter, skipinitialspace=True)

        name = int(text) - 1 if (text := self.form.PointNameLE.text()).isdigit() else None
        northing = int(text) - 1 if (text := self.form.NorthingLE.text()).isdigit() else None
        easting = int(text) - 1 if (text := self.form.EastingLE.text()).isdigit() else None
        elevation = int(text) - 1 if (text := self.form.ElevationLE.text()).isdigit() else None
        description = int(text) - 1 if (text := self.form.DescriptionLE.text()).isdigit() else None

        indices = [name, northing, easting, elevation, description]

        if operation == "Preview":
            self.preview_data(reader, indices)
        elif operation == "Import":
            self.import_data(reader, indices)

    def preview_data(self, reader, indices):
        """Fill the preview table with file data."""
        table_widget = self.form.PreviewTW
        table_widget.setRowCount(0)
        for row in reader:
            numRows = table_widget.rowCount()
            table_widget.insertRow(numRows)
            for col, index in enumerate(indices):
                if index is None: continue
                if index < len(row):
                    table_widget.setItem(numRows, col, QtWidgets.QTableWidgetItem(row[index]))

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
        selected_file = self.form.SelectedFilesLW.selectedItems()
        if selected_file:
            file_path = selected_file[0].text()
            self.form.PreviewL.setText(f"Preview: {os.path.basename(file_path)}")
            with open(file_path, 'r') as file:
                self.file_reader(file, "Preview")

    def get_selected_group(self):
        """Get the currently selected cluster."""
        if self.form.PointGroupChB.isChecked():
            return self.group_dict.get(self.form.SubGroupListCB.currentText())
        return make_geopoints.create()

    def accept(self):
        """Accept and process the selected files for import."""
        if self.form.SelectedFilesLW.count() == 0:
            FreeCAD.Console.PrintMessage("No Files selected\n")
            return

        for i in range(self.form.SelectedFilesLW.count()):
            file_path = self.form.SelectedFilesLW.item(i).text()
            with open(file_path, 'r') as file:
                self.file_reader(file, "Import")

        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()

    def needsFullSpace(self):
        return True