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

"""Provides the task panel code for the Cluster Exporter tool."""

import FreeCAD, FreeCADGui
from PySide import QtWidgets

from ..variables import ui_path
from .task_panel import TaskPanel
from ..utils import get_group


class TaskClusterExport(TaskPanel):
    def __init__(self):
        # Set UI.
        self.form = FreeCADGui.PySideUic.loadUi(ui_path + "/export_points.ui")
        self.form.BrowseB.clicked.connect(self.file_destination)

        # Add point groups to QListWidget
        clusters = get_group.get("Clusters")
        self.group_dict = {
            child.Label: child for child in clusters.Group if child.Proxy.Type == "Road::Cluster"
        }
        self.form.PointGroupsLW.addItems(self.group_dict.keys())

    def file_destination(self):
        """Get file destination."""

        # Select file
        parameter = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/General")
        path = parameter.GetString("FileOpenSavePath")
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
            None, "Save File", path, "Text Files (*.txt);;All Files (*)")

        if file_name:
            self.form.FileDestinationLE.setText(
                file_name if file_name.endswith(".txt") else file_name + ".txt")

            self.form.FileDestinationLE.setText(file_name)

    def accept(self):
        """Export selected point group(s)."""

        # Get user inputs
        line_edit = self.form.FileDestinationLE
        if not line_edit.text().strip() or self.form.PointGroupsLW.count() < 1:
            FreeCAD.Console.PrintError("No file destination or point groups found!\n")
            return

        # Set delimiter
        delimiter_map = {"White Space": ' ', "Comma": ','}
        delimiter = delimiter_map.get(self.form.DelimiterCB.currentText(), ' ')

        # Retrieve index inputs from user
        try:
            indexes = [
                int(self.form.PointNameLE.text()) - 1,
                int(self.form.NorthingLE.text()) - 1,
                int(self.form.EastingLE.text()) - 1,
                int(self.form.ElevationLE.text()) - 1,
                int(self.form.DescriptionLE.text()) - 1]

        except ValueError:
            FreeCAD.Console.PrintError("Please enter valid integer indices.\n")
            return

        try:
            with open(line_edit.text(), 'w') as file:
                # Get selected point groups
                for selection in self.form.PointGroupsLW.selectedIndexes():
                    cluster = self.group_dict[selection.data()]

                    # Print points to the file
                    for geopoint in cluster.Group:
                        # Create data list based on geopoint attributes
                        datas = [
                            geopoint.Label,                        # PointName
                            f"{geopoint.Shape.Point.x/1000:.3f}",  # Northing
                            f"{geopoint.Shape.Point.y/1000:.3f}",  # Easting
                            f"{geopoint.Shape.Point.z/1000:.3f}",  # Elevation
                            geopoint.Description or ""]            # Description

                        # Write data based on user-specified indexes
                        ordered_data = [None] * 5
                        for data, index in zip(datas, indexes):
                            ordered_data[index] = data

                        file.write(delimiter.join(ordered_data) + "\n")
            FreeCADGui.Control.closeDialog()

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error opening file: {e}\n")