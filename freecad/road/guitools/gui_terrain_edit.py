# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to edit Terrain objects."""

import FreeCAD, FreeCADGui
from pivy import coin
import os
from .. import ICONPATH
from ..utils.trackers import ViewTracker


class TerrainAddPoint:
    """Command to add a point to Terrain."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "TerrainAddPoint.svg"),
            "MenuText": "Add Point",
            "ToolTip": "Add a point to selected Terrain."
            }

    def Activated(self):
        self.terrain = FreeCADGui.Selection.getSelection()[-1]
        view = FreeCADGui.ActiveDocument.ActiveView
        tracker = ViewTracker(view, "Mouse", key="Left", function=self.add_point)
        tracker.start()

    def add_point(self, callback):
        """Add a point to the selected triangle"""
        picked_point = callback.getPickedPoint()
        if picked_point:
            detail = picked_point.getDetail()
            if detail.isOfType(coin.SoFaceDetail.getClassTypeId()):
                face_detail = coin.cast(detail, str(detail.getTypeId().getName()))
                index = face_detail.getFaceIndex()

                point = picked_point.getPoint().getValue()
                vector = FreeCAD.Vector(*point)

                origin = FreeCAD.ActiveDocument.getObject("GeoOrigin")
                vector = vector.add(origin.Base)
                operations = self.terrain.Operations
                operations.append({"type":"Add Point", "index":index, "vector":[*vector]})
                self.terrain.Operations = operations


class TerrainDeleteTriangle:
    """Command to delete a triangle from Terrain."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "TerrainDeleteTriangle.svg"),
            "MenuText": "Delete Triangle",
            "ToolTip": "Delete triangles from selected Terrain."
              }

    def Activated(self):
        self.terrain = FreeCADGui.Selection.getSelection()[-1]
        view = FreeCADGui.ActiveDocument.ActiveView
        tracker = ViewTracker(view, "Mouse", key="Left", function=self.delete_triangle)
        tracker.start()

    def delete_triangle(self, callback):
        """Delete selected triangle"""
        picked_point = callback.getPickedPoint()
        if picked_point:
            detail = picked_point.getDetail()
            if detail.isOfType(coin.SoFaceDetail.getClassTypeId()):
                face_detail = coin.cast(detail, str(detail.getTypeId().getName()))
                index = face_detail.getFaceIndex()

                operations = self.terrain.Operations
                operations.append({"type":"Delete Triangle", "index":index})
                self.terrain.Operations = operations


class TerrainSwapEdge:
    """Command to swap an edge between two triangles"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "TerrainSwapEdge.svg"),
            "MenuText": "Swap Edge",
            "ToolTip": "Swap Edge of selected Terrain."
            }

    def Activated(self):
        self.terrain = FreeCADGui.Selection.getSelection()[-1]
        view = FreeCADGui.ActiveDocument.ActiveView
        tracker = ViewTracker(view, "Mouse", key="Left", function=self.swap_edge)
        tracker.start()

    def swap_edge(self, callback):
        """Swap edge between two triangles"""
        picked_point = callback.getPickedPoint()
        if picked_point:
            detail = picked_point.getDetail()
            if detail.isOfType(coin.SoFaceDetail.getClassTypeId()):
                face_detail = coin.cast(detail, str(detail.getTypeId().getName()))
                index = face_detail.getFaceIndex()

                point = picked_point.getPoint().getValue()
                vector = FreeCAD.Vector(*point)

                facet = self.terrain.Mesh.Facets[index]
                min_distance = float("inf")
                other = -1

                for i in range(3):
                    edge = facet.getEdge(i)
                    distance = vector.distanceToLineSegment(*[FreeCAD.Vector(*point) for point in edge.Points])
                    if distance.Length < min_distance:
                        min_distance = distance.Length
                        other = facet.NeighbourIndices[i] 

                operations = self.terrain.Operations
                operations.append({"type":"Swap Edge", "index":index, "other":other})
                self.terrain.Operations = operations



class TerrainSmooth:
    """Command to smooth Terrain."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "TerrainSmooth.svg"),
            "MenuText": "Smooth Terrain",
            "ToolTip": "Smooth selected Terrain."
            }

    def Activated(self):
        terrain = FreeCADGui.Selection.getSelection()[-1]
        terrain.Mesh.smooth()


class TerrainEditGroup:
    """Gui Command group for the Arc tools."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "TerrainEdit.svg"),
            "MenuText": "Edit Surface",
            "ToolTip": "Edit surfaces."}

    def GetCommands(self):
        return ("Add Point",
                "Delete Triangle",
                "Swap Edge",
                "Smooth Terrain")

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            selection = FreeCADGui.Selection.getSelection()
            if selection:
                if selection[-1].Proxy.Type == "Road::Terrain":
                    return True
        return False


FreeCADGui.addCommand("Add Point", TerrainAddPoint())
FreeCADGui.addCommand("Delete Triangle", TerrainDeleteTriangle())
FreeCADGui.addCommand("Swap Edge", TerrainSwapEdge())
FreeCADGui.addCommand("Smooth Terrain", TerrainSmooth())
FreeCADGui.addCommand("Terrain Edit", TerrainEditGroup())