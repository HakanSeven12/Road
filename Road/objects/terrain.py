# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Terrain objects."""

import FreeCAD, Mesh, Part, MeshGui
from.geo_object import GeoObject
from ..functions.terrain_functions import (
    test_triangulation, 
    get_contours, 
    get_boundary)

import numpy
from scipy.spatial import Delaunay


class Terrain(GeoObject):
    """This class is about Terrain Object data features."""

    def __init__(self, obj):
        """Set data properties."""
        super().__init__(obj)

        self.Type = "Road::Terrain"

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
        if not obj.Clusters: return
        points = {}
        idx = 0
        for geopoints in obj.Clusters:
            for point in geopoints.Model.values():
                points[str(idx)] = [point['Easting']*1000, point['Northing']*1000, point['Elevation']*1000]
                idx += 1

        if len(points) < 3:
            obj.Mesh = Mesh.Mesh()
            obj.Contour = Part.Shape()
            obj.Boundary = Part.Shape()
            return

        if obj.Points == points: return

        tri = Delaunay(numpy.array(list(points.values()))[:, :-1])
        tested_tri = test_triangulation(tri, obj.MaxLength, obj.MaxAngle)

        faces = [[str(x) for x in f] for f in tri.simplices.tolist()]

        obj.Points = points
        obj.Faces = {"Visible": faces, "Invisible": []}

    def onChanged(self, obj, prop):
        """Do something when a data property has changed."""
        super().onChanged(obj, prop)

        if prop in ["Points", "Faces", "Operations"]:
            mesh = Mesh.Mesh()
            origin = None

            for face in obj.Faces["Visible"]:
                if origin is None:
                    origin = FreeCAD.Vector(obj.Points[face[0]])
                    origin.z = 0
                c1 = FreeCAD.Vector(obj.Points[face[0]]).sub(origin)
                c2 = FreeCAD.Vector(obj.Points[face[1]]).sub(origin)
                c3 = FreeCAD.Vector(obj.Points[face[2]]).sub(origin)
                mesh.addFacet(c1, c2, c3)

            for op in obj.Operations:
                if op.get("type") == "Add Point":
                    idx = op.get("index")
                    vec = FreeCAD.Vector(op.get("vector")).sub(obj.Geolocation.Base)
                    mesh.insertVertex(idx, vec)

                if op.get("type") == "Delete Triangle":
                    idx = op.get("index")
                    mesh.removeFacets([idx])

                if op.get("type") == "Swap Edge":
                    idx = op.get("index")
                    other = op.get("other")
                    try:
                        mesh.swapEdge(idx, other)

                    except Exception:
                        print("The edge between these triangles cannot be swappable")

            if mesh.CountFacets > 0:
                obj.Geolocation.Base = origin
                mesh.Placement = obj.Placement
                obj.Mesh = mesh
        
        elif prop == "Mesh":
            mesh = obj.getPropertyByName(prop)
            obj.Contour = get_contours(mesh, obj.MajorInterval.Value, obj.MinorInterval.Value)
            obj.Boundary = get_boundary(mesh)

        elif prop == "MinorInterval":
            obj.MajorInterval = obj.getPropertyByName(prop) * 5
