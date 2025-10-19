# SPDX-License-Identifier: LGPL-2.1-or-later

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
            "App::PropertyLinkList", "Clusters", "Base",
            "Clusters added to the Delaunay triangulation").Clusters = []

        obj.addProperty(
            "App::PropertyPythonObject", "Points", "Triangulation",
            "Points of triangulation").Points = {}

        obj.addProperty(
            "App::PropertyPythonObject", "Faces", "Triangulation",
            "Faces of triangulation").Faces = {"Visible":[], "Invisible":[]}

        obj.addProperty(
            "App::PropertyPythonObject", "Operations", "Triangulation",
            "Terrain edit operations").Operations = []

        obj.addProperty(
            "Mesh::PropertyMeshKernel", "Mesh", "Triangulation",
            "Mesh object of triangulation").Mesh = Mesh.Mesh()

        obj.addProperty(
            "App::PropertyLength", "MaxLength", "Constraint",
            "Maximum length of triangle edge").MaxLength = 500000

        obj.addProperty(
            "App::PropertyAngle","MaxAngle","Constraint",
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
        pass

    def onChanged(self, obj, prop):
        """Do something when a data property has changed."""
        if prop == "Points" or prop == "Faces":
            mesh_obj = Mesh.Mesh()
            origin = None

            for face in obj.Faces["Visible"]:
                if origin is None:
                    origin = FreeCAD.Vector(obj.Points[face[0]])
                    origin.z = 0
                c1 = FreeCAD.Vector(obj.Points[face[0]]).sub(origin)
                c2 = FreeCAD.Vector(obj.Points[face[1]]).sub(origin)
                c3 = FreeCAD.Vector(obj.Points[face[2]]).sub(origin)
                mesh_obj.addFacet(c1, c2, c3)

            if mesh_obj.CountFacets > 0:
                obj.Placement.Base = origin
                obj.Mesh = mesh_obj

        if prop in ["Operations"]:
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
