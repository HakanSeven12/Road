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

"""Provides GUI tools to demolish Terrain objects."""

import FreeCAD, FreeCADGui

import Part, Mesh

from ..variables import icons_path


class TerrainExtractPoints:
    """Command to extract Points from Terrain."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/TerrainExtractPoints.svg",
            "MenuText": "Extract Points",
            "ToolTip": "Extract Points from selected Terrain."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return True

    def Activated(self):
        """Command activation method"""
        terrain = FreeCADGui.Selection.getSelection()[0]
        for p in terrain.Mesh.Topology[0]:
            point = Part.Vertex(p)
            Part.show(point)


class TerrainExtractTrianglesMesh:
    """Command to extract Triangles(Mesh) from Terrain."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/TerrainExtractTrianglesMesh.svg",
            "MenuText": "Extract Triangles(Mesh)",
            "ToolTip": "Extract Triangles(Mesh) from selected Terrain."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return True

    def Activated(self):
        """Command activation method"""
        terrain = FreeCADGui.Selection.getSelection()[0]
        Mesh.show(terrain.Mesh)


class TerrainExtractTrianglesShape:
    """Command to extract Triangles(Shape) from Terrain."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/TerrainExtractTrianglesShape.svg",
            "MenuText": "Extract Triangles(Shape)",
            "ToolTip": "Extract Triangles(Shape) from selected Terrain."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return True

    def Activated(self):
        """Command activation method"""
        shape = Part.Shape()
        terrain = FreeCADGui.Selection.getSelection()[0]
        shape.makeShapeFromMesh(terrain.Mesh.Topology, 1)
        Part.show(shape)


class TerrainExtractBoundary:
    """Command to extract Boundary from Terrain."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/TerrainExtractBoundary.svg",
            "MenuText": "Extract Boundary",
            "ToolTip": "Extract Boundary from selected Terrain."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return True

    def Activated(self):
        """Command activation method"""
        terrain = FreeCADGui.Selection.getSelection()[0]
        Part.show(terrain.Boundary)


class TerrainExtractContours:
    """Command to extract Contours from Terrain."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/TerrainExtractContours.svg",
            "MenuText": "Extract Contours",
            "ToolTip": "Extract Contours from selected Terrain."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return True

    def Activated(self):
        """Command activation method"""
        terrain = FreeCADGui.Selection.getSelection()[0]
        Part.show(terrain.Contour)


class TerrainDemolishGroup:
    """Gui Command group for the Terrain Demolish tools."""

    def GetResources(self):
        """Set icon, menu and tooltip."""
        return {
            "Pixmap": icons_path + "/TerrainDemolish.svg",
            "MenuText": "Demolish Terrain",
            "ToolTip": "Extract subelements of the selected Terrain."}

    def GetCommands(self):
        """Return a tuple of commands in the group."""
        return ("Terrain Extract Points",
                "Terrain Extract Triangles(Mesh)",
                "Terrain Extract Triangles(Shape)",
                "Terrain Extract Boundary",
                "Terrain Extract Contours")

    def IsActive(self):
        """Return True when this command should be available."""
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