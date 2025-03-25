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

import FreeCAD
import Mesh, Part
import MeshGui

import numpy
from scipy.spatial import Delaunay
from ..functions.terrain_functions import (
    test_triangulation, 
    get_contours, 
    get_boundary)


class Terrain:
    """This class is about Terrain Object data features."""

    def __init__(self, obj):
        """Set data properties."""
        self.Type = "Road::Terrain"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "App::PropertyVectorList", "Points", "Triangulation",
            "Clusters added to the Delaunay triangulation", attr=16).Points = []

        obj.addProperty(
            "App::PropertyLinkList", "Clusters", "Triangulation",
            "Clusters added to the Delaunay triangulation").Clusters = []

        obj.addProperty(
            "App::PropertyPythonObject", "Operations", "Triangulation",
            "Terrain edit operations").Operations = []

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

    def execute(self, obj):
        """Do something when doing a recomputation."""
        points = []
        for cluster in obj.Clusters:
            for geopoint in cluster.Group:
                points.append(geopoint.Placement.Base)

        if obj.Points == points: return
        obj.Points = points

    def onChanged(self, obj, prop):
        """Do something when a data property has changed."""
        if prop in ["Points", "Operations"]:
            points = obj.Points

            if len(points) < 3:
                obj.Mesh = Mesh.Mesh()
                obj.Contour = Part.Shape()
                obj.Boundary = Part.Shape()
                return

            obj.Placement.Base = points[0]
            obj.Placement.Base.z = 0

            tri = Delaunay(numpy.array([[point.x, point.y] for point in points]))
            tested_tri = test_triangulation(tri, obj.MaxLength, obj.MaxAngle)

            points = [point.sub(obj.Placement.Base) for point in points]
            mesh = Mesh.Mesh([points[i] for i in tested_tri])

            for op in obj.Operations:
                if op.get("type") == "Add Point":
                    idx = op.get("index")
                    vec = op.get("vector").add(obj.Placement.Base.negative())
                    mesh.insertVertex(idx, vec)

                if op.get("type") == "Delete Triangle":
                    idx = op.get("index")
                    mesh.removeFacets([idx])

                if op.get("type") == "Swap Edge":
                    idx = op.get("index")
                    other = op.get("other")
                    print(idx,other)
                    """
                    try:
                        mesh.swapEdge(idx, other)

                    except Exception:
                        print("The edge between these triangles cannot be swappable")
                    """

            obj.Mesh = mesh
        
        elif prop == "Mesh":
            mesh = obj.getPropertyByName(prop)
            obj.Contour = get_contours(mesh, obj.MajorInterval.Value, obj.MinorInterval.Value)
            obj.Boundary = get_boundary(mesh)

        elif prop == "MinorInterval":
            obj.MajorInterval = obj.getPropertyByName(prop) * 5
