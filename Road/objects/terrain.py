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

"""Provides the object code for Terrain objects."""

import Mesh, Part
import MeshGui

import numpy
from scipy.spatial import Delaunay
from ..utils.get_group import georigin
from ..functions.terrain_functions import (
    test_triangulation, 
    get_contours, 
    get_boundary)


class Terrain:
    """This class is about Terrain Object data features."""

    def __init__(self, obj):
        """Set data properties."""
        self.Type = "Road::Terrain"

        # Triangulation properties.
        obj.addProperty(
            "App::PropertyLinkList", "Clusters", "Triangulation",
            "Clusters added to the Delaunay triangulation").Clusters = []

        obj.addProperty(
            "App::PropertyPythonObject", "AddPoints", "Triangulation",
            "Points added to the triangulation").AddPoints = {}

        obj.addProperty(
            "App::PropertyVectorList", "DeletePoints", "Triangulation",
            "Points deleted from the triangulation").DeletePoints = []

        obj.addProperty(
            "App::PropertyVectorList", "SwapEdges", "Triangulation",
            "Edges swapped in the triangulation").SwapEdges = []

        obj.addProperty(
            "Mesh::PropertyMeshKernel", "Mesh", "Triangulation",
            "Mesh object of triangulation").Mesh = Mesh.Mesh()

        obj.addProperty(
            "App::PropertyLength", "MaxLength", "Triangulation",
            "Maximum length of triangle edge").MaxLength = 500000

        obj.addProperty(
            "App::PropertyAngle","MaxAngle","Triangulation",
            "Maximum angle of triangle edge").MaxAngle = 180

        obj.addProperty("Part::PropertyPartShape", "Boundary", "Triangulation",
            "Boundary Shapes").Boundary = Part.Shape()

        # Analysis properties.
        obj.addProperty(
            "App::PropertyEnumeration", "AnalysisType", "Analysis",
            "Set analysis type").AnalysisType = ["Default", "Elevation", "Slope", "Direction"]

        obj.addProperty(
            "App::PropertyInteger", "Ranges", "Analysis",
            "Ranges").Ranges = 5

        # Contour properties.
        obj.addProperty("Part::PropertyPartShape", "Contour", "Contour",
            "Contour Shapes").Contour = Part.Shape()

        obj.addProperty(
            "App::PropertyLength", "MajorInterval", "Contour",
            "Major contour interval").MajorInterval = 5000

        obj.addProperty(
            "App::PropertyLength", "MinorInterval", "Contour",
            "Minor contour interval").MinorInterval = 1000

        obj.Proxy = self

    def onChanged(self, obj, prop):
        """Do something when a data property has changed."""
        if prop == "MinorInterval":
            obj.MajorInterval = obj.getPropertyByName(prop) * 5

    def execute(self, obj):
        """Do something when doing a recomputation."""
        points = []
        for cluster in obj.Clusters:
            for geopoint in cluster.Group:
                points.append(geopoint.Placement.Base)

        if len(points) < 3:
            obj.Mesh = Mesh.Mesh()
            obj.Contour = Part.Shape()
            obj.Boundary = Part.Shape()
            return

        tri = Delaunay(numpy.array([[point.x, point.y] for point in points]))
        tested_tri = test_triangulation(tri, obj.MaxLength, obj.MaxAngle)

        origin = georigin(points[0])
        points = [point.sub(origin.Base) for point in points]
        obj.Mesh = Mesh.Mesh([points[i] for i in tested_tri])

        obj.Contour = get_contours(obj.Mesh, obj.MajorInterval.Value, obj.MinorInterval.Value)
        obj.Boundary = get_boundary(obj.Mesh)
