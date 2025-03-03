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

"""Provides the task panel code for the Cluster Importer tool."""

import FreeCAD, FreeCADGui
from PySide import QtCore, QtWidgets
import csv, os

from ..variables import ui_path
from .task_panel import TaskPanel
from ..utils import get_group
from ..make import make_cluster, make_geopoint


class TaskClusterImport(TaskPanel):
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
            cluster.Label: cluster for cluster in clusters.Group if cluster.Proxy.Type == 'Road::Cluster'
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
        new_group = make_cluster.create(group_name)
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
        for row in reader:
            geopoint = make_geopoint.create(
                row[indices[0]] if indices[0] else "GeoPoint", 
                float(row[indices[1]]), 
                float(row[indices[2]]), 
                float(row[indices[3]]) if indices[3] else 0.00, 
                row[indices[4]] if indices[4] else "")

            cluster.addObject(geopoint)

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
        return make_cluster.create()

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
