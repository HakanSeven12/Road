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

"""Provides the viewprovider code for Terrain objects."""

import FreeCAD
from pivy import coin
import random

from ..variables import icons_path, line_patterns
from ..utils.get_group import georigin
from ..functions.terrain_functions import wire_view, elevation_analysis, slope_analysis, direction_analysis


class ViewProviderTerrain:
    """
    This class is about Terrain Object view features.
    """

    def __init__(self, vobj):
        '''
        Set view properties.
        '''
        (r, g, b) = (random.random(), random.random(), random.random())

        # Triangulation properties.
        vobj.addProperty(
            "App::PropertyIntegerConstraint", "Transparency", "Terrain Style",
            "Set triangle face transparency").Transparency = (50, 0, 100, 1)

        vobj.addProperty(
            "App::PropertyColor", "ShapeColor", "Terrain Style",
            "Set triangle face color").ShapeColor = (r, g, b, vobj.Transparency/100)

        vobj.addProperty(
            "App::PropertyMaterial", "ShapeMaterial", "Terrain Style",
            "Triangle face material").ShapeMaterial = FreeCAD.Material()

        vobj.addProperty(
            "App::PropertyIntegerConstraint", "LineTransparency", "Terrain Style",
            "Set triangle edge transparency").LineTransparency = (50, 0, 100, 1)

        vobj.addProperty(
            "App::PropertyColor", "LineColor", "Terrain Style",
            "Set triangle face color").LineColor = (0.5, 0.5, 0.5, vobj.LineTransparency/100)

        vobj.addProperty(
            "App::PropertyMaterial", "LineMaterial", "Terrain Style",
            "Triangle face material").LineMaterial = FreeCAD.Material()

        vobj.addProperty(
            "App::PropertyFloatConstraint", "LineWidth", "Terrain Style",
            "Set triangle edge line width").LineWidth = (0.0, 1.0, 20.0, 1.0)

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
        vobj.ShapeMaterial.DiffuseColor = vobj.ShapeColor

    def attach(self, vobj):
        '''
        Create Object visuals in 3D view.
        '''
        # GeoCoords Node.
        self.geo_coords = coin.SoGeoCoordinate()

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
        self.boundary_coords = coin.SoGeoCoordinate()
        self.boundary_lines = coin.SoLineSet()
        self.boundary_style = coin.SoDrawStyle()
        self.boundary_style.style = coin.SoDrawStyle.LINES

        # Boundary root.
        boundaries = coin.SoType.fromName('SoFCSelection').createInstance()
        boundaries.style = 'EMISSIVE_DIFFUSE'
        boundaries.addChild(self.boundary_color)
        boundaries.addChild(self.boundary_style)
        boundaries.addChild(self.boundary_coords)
        boundaries.addChild(self.boundary_lines)

        # Major Contour features.
        self.major_color = coin.SoBaseColor()
        self.major_coords = coin.SoGeoCoordinate()
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
        self.minor_coords = coin.SoGeoCoordinate()
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
        highlight = coin.SoType.fromName('SoFCSelection').createInstance()
        highlight.style = 'EMISSIVE_DIFFUSE'
        highlight.addChild(shape_hints)
        highlight.addChild(self.mat_binding)
        highlight.addChild(self.geo_coords)
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
        terrain_root = coin.SoSeparator()
        terrain_root.addChild(face)
        terrain_root.addChild(offset)
        terrain_root.addChild(edge)
        terrain_root.addChild(major_contours)
        terrain_root.addChild(minor_contours)
        vobj.addDisplayMode(terrain_root,"Terrain")

        # Boundary root.
        boundary_root = coin.SoSeparator()
        boundary_root.addChild(boundaries)
        vobj.addDisplayMode(boundary_root,"Boundary")

        # Elevation/Shaded root.
        shaded_root = coin.SoSeparator()
        shaded_root.addChild(face)
        #vobj.addDisplayMode(shaded_root,"Elevation")
        #vobj.addDisplayMode(shaded_root,"Slope")
        vobj.addDisplayMode(shaded_root,"Shaded")

        # Flat Lines root.
        flatlines_root = coin.SoSeparator()
        flatlines_root.addChild(face)
        flatlines_root.addChild(offset)
        flatlines_root.addChild(edge)
        vobj.addDisplayMode(flatlines_root,"Flat Lines")

        # Wireframe root.
        wireframe_root = coin.SoSeparator()
        wireframe_root.addChild(edge)
        wireframe_root.addChild(major_contours)
        wireframe_root.addChild(minor_contours)
        vobj.addDisplayMode(wireframe_root,"Wireframe")

        # Take features from properties.
        self.onChanged(vobj,"ShapeColor")
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

    def updateData(self, obj, prop):
        '''
        Update Object visuals when a data property changed.
        '''
        if prop == "Mesh":
            mesh = obj.getPropertyByName(prop)
            if not mesh.Topology[0]: return

            # Set System.
            origin = georigin(mesh.Topology[0][0])
            geo_system = ["UTM", origin.UtmZone, "FLAT"]
            self.geo_coords.geoSystem.setValues(geo_system)
            self.boundary_coords.geoSystem.setValues(geo_system)
            self.major_coords.geoSystem.setValues(geo_system)
            self.minor_coords.geoSystem.setValues(geo_system)

            triangles = []
            for i in mesh.Topology[1]:
                triangles.extend(list(i))
                triangles.append(-1)

            self.geo_coords.point.values = [point.add(origin.Base) for point in mesh.Topology[0]]
            self.triangles.coordIndex.values = triangles

        elif prop == "Contour":
            origin = georigin()
            shape = obj.getPropertyByName(prop)

            if shape.SubShapes:
                major = shape.SubShapes[0]
                points, vertices = wire_view(major)

                self.major_coords.point.values = [point.add(origin.Base) for point in points]
                self.major_lines.numVertices.values = vertices

                minor = shape.SubShapes[1]
                points, vertices = wire_view(minor)

                self.minor_coords.point.values = [point.add(origin.Base) for point in points]
                self.minor_lines.numVertices.values = vertices

        elif prop == "Boundary":
            origin = georigin()
            boundary = obj.getPropertyByName(prop)
            points, vertices = wire_view(boundary)

            self.boundary_coords.point.values = [point.add(origin.Base) for point in points]
            self.boundary_lines.numVertices.values = vertices
        
        elif prop == "AnalysisType" or prop == "Ranges":
            analysis_type = obj.getPropertyByName("AnalysisType")
            ranges = obj.getPropertyByName("Ranges")

            if analysis_type == "Default":
                if hasattr(obj.ViewObject, "ShapeMaterial"):
                    material = obj.ViewObject.ShapeMaterial
                    self.face_material.diffuseColor = material.DiffuseColor[:3]
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
        
    def onChanged(self, vobj, prop):
        '''
        Update Object visuals when a view property changed.
        '''
        if prop == "ShapeColor" or prop == "Transparency":
            if hasattr(vobj, "ShapeColor") and hasattr(vobj, "Transparency"):
                color = vobj.getPropertyByName("ShapeColor")
                transparency = vobj.getPropertyByName("Transparency")
                color = (color[0], color[1], color[2], transparency/100)
                vobj.ShapeMaterial.DiffuseColor = color

        if prop == "ShapeMaterial":
            if hasattr(vobj, "ShapeMaterial"):
                material = vobj.getPropertyByName(prop)
                self.face_material.diffuseColor.setValue(material.DiffuseColor[:3])
                self.face_material.transparency = material.DiffuseColor[3]

        if prop == "LineColor" or prop == "LineTransparency":
            if hasattr(vobj, "LineColor") and hasattr(vobj, "LineTransparency"):
                color = vobj.getPropertyByName("LineColor")
                transparency = vobj.getPropertyByName("LineTransparency")
                color = (color[0], color[1], color[2], transparency/100)
                vobj.LineMaterial.DiffuseColor = color

        if prop == "LineMaterial":
            material = vobj.getPropertyByName(prop)
            self.edge_material.diffuseColor.setValue(material.DiffuseColor[:3])
            self.edge_material.transparency = material.DiffuseColor[3]

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

    def getDisplayModes(self,vobj):
        '''
        Return a list of display modes.
        '''
        modes = ["Terrain", "Boundary", "Flat Lines", "Shaded", "Wireframe"]

        return modes

    def getDefaultDisplayMode(self):
        '''
        Return the name of the default display mode.
        '''
        return "Terrain"

    def setDisplayMode(self,mode):
        '''
        Map the display mode defined in attach with 
        those defined in getDisplayModes.
        '''
        return mode

    def getIcon(self):
        '''
        Return object treeview icon.
        '''
        return icons_path + '/Terrain.svg'

    def dumps(self):
        """Called during document saving"""
        return None

    def loads(self, state):
        """Called during document restore."""
        return None
