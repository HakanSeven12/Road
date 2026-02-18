# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to demolish Terrain objects."""

import FreeCAD, FreeCADGui
import Part, Mesh
import os
from .. import ICONPATH


class TerrainExtractPoints:
    """Command to extract Points from Terrain."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "TerrainExtractPoints.svg"),
            "MenuText": "Extract Points",
            "ToolTip": "Extract Points from selected Terrain."
            }

    def Activated(self):
        terrain = FreeCADGui.Selection.getSelection()[0]
        for p in terrain.Mesh.Topology[0]:
            point = Part.Vertex(p)
            Part.show(point)


class TerrainExtractTrianglesMesh:
    """Command to extract Triangles(Mesh) from Terrain."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "TerrainExtractTrianglesMesh.svg"),
            "MenuText": "Extract Triangles(Mesh)",
            "ToolTip": "Extract Triangles(Mesh) from selected Terrain."
            }

    def Activated(self):
        terrain = FreeCADGui.Selection.getSelection()[0]
        Mesh.show(terrain.Mesh)


class TerrainExtractTrianglesShape:
    """Command to extract Triangles(Shape) from Terrain."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "TerrainExtractTrianglesShape.svg"),
            "MenuText": "Extract Triangles(Shape)",
            "ToolTip": "Extract Triangles(Shape) from selected Terrain."
            }

    def Activated(self):
        shape = Part.Shape()
        terrain = FreeCADGui.Selection.getSelection()[0]
        shape.makeShapeFromMesh(terrain.Mesh.Topology, 1)
        Part.show(shape)


class TerrainExtractBoundary:
    """Command to extract Boundary from Terrain."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "TerrainExtractBoundary.svg"),
            "MenuText": "Extract Boundary",
            "ToolTip": "Extract Boundary from selected Terrain."
            }

    def Activated(self):
        terrain = FreeCADGui.Selection.getSelection()[0]
        Part.show(terrain.Boundary)


class TerrainExtractContours:
    """Command to extract Contours from Terrain."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "TerrainExtractContours.svg"),
            "MenuText": "Extract Contours",
            "ToolTip": "Extract Contours from selected Terrain."
            }

    def Activated(self):
        terrain = FreeCADGui.Selection.getSelection()[0]
        Part.show(terrain.Contour)


class TerrainDemolishGroup:
    """Gui Command group for the Terrain Demolish tools."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "TerrainDemolish.svg"),
            "MenuText": "Demolish Terrain",
            "ToolTip": "Extract subelements of the selected Terrain."}

    def GetCommands(self):
        return ("Terrain Extract Points",
                "Terrain Extract Triangles(Mesh)",
                "Terrain Extract Triangles(Shape)",
                "Terrain Extract Boundary",
                "Terrain Extract Contours")

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            selection = FreeCADGui.Selection.getSelection()
            if selection:
                if selection[-1].Proxy.Type == "Road::Terrain":
                    return True
        return False


FreeCADGui.addCommand("Terrain Extract Points", TerrainExtractPoints())
FreeCADGui.addCommand("Terrain Extract Triangles(Mesh)", TerrainExtractTrianglesMesh())
FreeCADGui.addCommand("Terrain Extract Triangles(Shape)", TerrainExtractTrianglesShape())
FreeCADGui.addCommand("Terrain Extract Boundary", TerrainExtractBoundary())
FreeCADGui.addCommand("Terrain Extract Contours", TerrainExtractContours())
FreeCADGui.addCommand("Terrain Demolish", TerrainDemolishGroup())