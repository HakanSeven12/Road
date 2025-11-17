# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Terrain objects."""

import FreeCAD
from pivy import coin
import random
from ..variables import line_patterns
from .view_geo_object import ViewProviderGeoObject
from ..functions.terrain_functions import (
    wire_view, 
    elevation_analysis, 
    slope_analysis, 
    direction_analysis)


class ViewProviderTerrain(ViewProviderGeoObject):
    """This class is about Terrain Object view features."""

    def __init__(self, vobj):
        """Set view properties."""
        super().__init__(vobj,"Terrain")

        (r, g, b) = (random.random(), random.random(), random.random())

        # Triangulation properties.
        vobj.addProperty(
            "App::PropertyMaterial", "LineMaterial", "Terrain Style",
            "Triangle face material").LineMaterial = FreeCAD.Material()

        # Boundary properties.
        vobj.addProperty(
            "App::PropertyColor", "BoundaryColor", "Boundary Style",
            "Set boundary contour color").BoundaryColor = (0.0, 0.75, 1.0, 0.0)

        vobj.addProperty(
            "App::PropertyFloatConstraint", "BoundaryWidth", "Boundary Style",
            "Set boundary contour line width").BoundaryWidth = (3.0, 1.0, 20.0, 1.0)

        vobj.addProperty(
            "App::PropertyEnumeration", "BoundaryPattern", "Boundary Style",
            "Set a line pattern for boundary").BoundaryPattern = [*line_patterns]

        vobj.addProperty(
            "App::PropertyIntegerConstraint", "PatternScale", "Boundary Style",
            "Scale the line pattern").PatternScale = (3, 1, 20, 1)

        # Contour properties.
        vobj.addProperty(
            "App::PropertyColor", "MajorColor", "Contour Style",
            "Set major contour color").MajorColor = (1.0, 0.0, 0.0, 0.0)

        vobj.addProperty(
            "App::PropertyFloatConstraint", "MajorWidth", "Contour Style",
            "Set major contour line width").MajorWidth = (4.0, 1.0, 20.0, 1.0)

        vobj.addProperty(
            "App::PropertyColor", "MinorColor", "Contour Style",
            "Set minor contour color").MinorColor = (1.0, 1.0, 0.0, 0.0)

        vobj.addProperty(
            "App::PropertyFloatConstraint", "MinorWidth", "Contour Style",
            "Set major contour line width").MinorWidth = (2.0, 1.0, 20.0, 1.0)

        vobj.Proxy = self
        vobj.Transparency = 50

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        super().attach(vobj)

        # GeoCoords Node.
        self.terrain_coords = coin.SoCoordinate3()

        # Terrain features.
        self.triangles = coin.SoIndexedFaceSet()
        self.face_material = coin.SoMaterial()
        self.edge_material = coin.SoMaterial()
        self.edge_color = coin.SoBaseColor()
        self.edge_style = coin.SoDrawStyle()
        self.edge_style.style = coin.SoDrawStyle.LINES

        shape_hints = coin.SoShapeHints()
        shape_hints.vertex_ordering = coin.SoShapeHints.COUNTERCLOCKWISE
        self.mat_binding = coin.SoMaterialBinding()
        self.mat_binding.value = coin.SoMaterialBinding.OVERALL
        offset = coin.SoPolygonOffset()
        offset.styles = coin.SoPolygonOffset.LINES
        offset.factor = -2.0

        # Boundary features.
        self.boundary_color = coin.SoBaseColor()
        self.boundary_coords = coin.SoCoordinate3()
        self.boundary_lines = coin.SoLineSet()
        self.boundary_style = coin.SoDrawStyle()
        self.boundary_style.style = coin.SoDrawStyle.LINES

        # Boundary root.
        boundaries = coin.SoType.fromName("SoFCSelection").createInstance()
        boundaries.style = "EMISSIVE_DIFFUSE"
        boundaries.addChild(self.boundary_color)
        boundaries.addChild(self.boundary_style)
        boundaries.addChild(self.boundary_coords)
        boundaries.addChild(self.boundary_lines)

        # Major Contour features.
        self.major_color = coin.SoBaseColor()
        self.major_coords = coin.SoCoordinate3()
        self.major_lines = coin.SoLineSet()
        self.major_style = coin.SoDrawStyle()
        self.major_style.style = coin.SoDrawStyle.LINES

        # Major Contour root.
        major_contours = coin.SoSeparator()
        major_contours.addChild(self.major_color)
        major_contours.addChild(self.major_style)
        major_contours.addChild(self.major_coords)
        major_contours.addChild(self.major_lines)

        # Minor Contour features.
        self.minor_color = coin.SoBaseColor()
        self.minor_coords = coin.SoCoordinate3()
        self.minor_lines = coin.SoLineSet()
        self.minor_style = coin.SoDrawStyle()
        self.minor_style.style = coin.SoDrawStyle.LINES

        # Minor Contour root.
        minor_contours = coin.SoSeparator()
        minor_contours.addChild(self.minor_color)
        minor_contours.addChild(self.minor_style)
        minor_contours.addChild(self.minor_coords)
        minor_contours.addChild(self.minor_lines)

        # Highlight for selection.
        highlight = coin.SoType.fromName("SoFCSelection").createInstance()
        highlight.style = "EMISSIVE_DIFFUSE"
        highlight.addChild(shape_hints)
        highlight.addChild(self.mat_binding)
        highlight.addChild(self.terrain_coords)
        highlight.addChild(self.triangles)
        highlight.addChild(boundaries)

        # Face root.
        face = coin.SoSeparator()
        face.addChild(self.face_material)
        face.addChild(highlight)

        # Edge root.
        edge = coin.SoSeparator()
        edge.addChild(self.edge_material)
        edge.addChild(self.edge_style)
        edge.addChild(highlight)

        # Terrain root.
        self.standard.addChild(face)
        self.standard.addChild(offset)
        self.standard.addChild(edge)
        self.standard.addChild(major_contours)
        self.standard.addChild(minor_contours)

        # Boundary root.
        self.flat_lines.addChild(boundaries)

        # Wireframe root.
        self.wireframe.addChild(edge)
        self.wireframe.addChild(major_contours)
        self.wireframe.addChild(minor_contours)

        # Take features from properties.
        self.onChanged(vobj,"ShapeAppearance")
        self.onChanged(vobj,"LineColor")
        self.onChanged(vobj,"LineWidth")
        self.onChanged(vobj,"BoundaryColor")
        self.onChanged(vobj,"BoundaryWidth")
        self.onChanged(vobj,"BoundaryPattern")
        self.onChanged(vobj,"PatternScale")
        self.onChanged(vobj,"MajorColor")
        self.onChanged(vobj,"MajorWidth")
        self.onChanged(vobj,"MinorColor")
        self.onChanged(vobj,"MinorWidth")

    def onChanged(self, vobj, prop):
        """Update Object visuals when a view property changed."""

        if prop == "ShapeAppearance":
            material = vobj.ShapeAppearance[0]
            self.face_material.diffuseColor.setValue(material.DiffuseColor[:3])
            self.face_material.ambientColor.setValue(material.AmbientColor[:3])
            self.face_material.specularColor.setValue(material.SpecularColor[:3])
            self.face_material.emissiveColor.setValue(material.EmissiveColor[:3])
            self.face_material.shininess.setValue(material.Shininess)
            self.face_material.transparency.setValue(material.Transparency)

        if prop == "LineMaterial":
            self.edge_material.diffuseColor.setValue(vobj.LineMaterial.DiffuseColor[:3])
            self.edge_material.transparency = vobj.LineMaterial.DiffuseColor[3]

        if prop == "LineWidth":
            width = vobj.getPropertyByName(prop)
            self.edge_style.lineWidth = width

        if prop == "BoundaryColor":
            color = vobj.getPropertyByName(prop)
            self.boundary_color.rgb = color[:3]

        if prop == "BoundaryWidth":
            width = vobj.getPropertyByName(prop)
            self.boundary_style.lineWidth = width

        if prop == "BoundaryPattern":
            if hasattr(vobj, "BoundaryPattern"):
                pattern = vobj.getPropertyByName(prop)
                self.boundary_style.linePattern = line_patterns[pattern]

        if prop == "PatternScale":
            if hasattr(vobj, "PatternScale"):
                scale = vobj.getPropertyByName(prop)
                self.boundary_style.linePatternScaleFactor = scale

        if prop == "MajorColor":
            color = vobj.getPropertyByName(prop)
            self.major_color.rgb = color[:3]

        if prop == "MajorWidth":
            width = vobj.getPropertyByName(prop)
            self.major_style.lineWidth = width

        if prop == "MinorColor":
            color = vobj.getPropertyByName(prop)
            self.minor_color.rgb = color[:3]

        if prop == "MinorWidth":
            width = vobj.getPropertyByName(prop)
            self.minor_style.lineWidth = width

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        super().updateData(obj, prop)

        if prop == "Mesh":
            mesh = obj.getPropertyByName(prop)
            print(mesh.Topology[0])
            self.terrain_coords.point.values = mesh.Topology[0]
            self.triangles.coordIndex.values = [x for i in mesh.Topology[1] for x in (*i, -1)]

        elif prop == "Contour":
            shape = obj.getPropertyByName(prop)

            if shape.SubShapes:
                major = shape.SubShapes[0]
                points, vertices = wire_view(major)

                self.major_coords.point.values = points
                self.major_lines.numVertices.values = vertices

                minor = shape.SubShapes[1]
                points, vertices = wire_view(minor)

                self.minor_coords.point.values = points
                self.minor_lines.numVertices.values = vertices

        elif prop == "Boundary":
            boundary = obj.getPropertyByName(prop)
            points, vertices = wire_view(boundary)

            self.boundary_coords.point.values = points
            self.boundary_lines.numVertices.values = vertices
        
        elif prop == "AnalysisType" or prop == "Ranges":
            analysis_type = obj.getPropertyByName("AnalysisType")
            ranges = obj.getPropertyByName("Ranges")

            if analysis_type == "Default":
                material = obj.ViewObject.ShapeAppearance[0]
                self.face_material.diffuseColor.setValue(material.DiffuseColor[:3])
                self.face_material.ambientColor.setValue(material.AmbientColor[:3])
                self.face_material.specularColor.setValue(material.SpecularColor[:3])
                self.face_material.emissiveColor.setValue(material.EmissiveColor[:3])
                self.face_material.shininess = material.Shininess
                self.face_material.transparency = material.Transparency

                self.mat_binding.value = coin.SoMaterialBinding.OVERALL

            elif analysis_type == "Elevation":
                colorlist = elevation_analysis(obj.Mesh, ranges)
                self.mat_binding.value = coin.SoMaterialBinding.PER_FACE
                self.face_material.diffuseColor.setValues(0,len(colorlist),colorlist)

            elif analysis_type == "Slope":
                colorlist = slope_analysis(obj.Mesh, ranges)
                self.mat_binding.value = coin.SoMaterialBinding.PER_FACE
                self.face_material.diffuseColor.setValues(0,len(colorlist),colorlist)

            elif analysis_type == "Direction":
                colorlist = direction_analysis(obj.Mesh, ranges)
                self.mat_binding.value = coin.SoMaterialBinding.PER_FACE
                self.face_material.diffuseColor.setValues(0,len(colorlist),colorlist)