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

"""Provides GUI tools to edit Terrain objects."""

import FreeCAD, FreeCADGui
from pivy import coin

from ..variables import icons_path
from ..utils.trackers import ViewTracker


class TerrainAddPoint:
    """Command to add a point to Terrain."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/AddTriangle.svg",
            "MenuText": "Add Point",
            "ToolTip": "Add a point to selected Terrain."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return True

    def Activated(self):
        """Command activation method"""
        self.terrain = FreeCADGui.Selection.getSelection()[-1]
        tracker = ViewTracker("Mouse", key="Left", function=self.add_point)
        tracker.start()

    def add_point(self, callback):
        """Take two triangle by mouse clicks and swap edge between them"""
        picked_point = callback.getPickedPoint()
        if picked_point:
            detail = picked_point.getDetail()
            if detail.isOfType(coin.SoFaceDetail.getClassTypeId()):
                face_detail = coin.cast(detail, str(detail.getTypeId().getName()))
                index = face_detail.getFaceIndex()

                point = picked_point.getPoint().getValue()
                vector = FreeCAD.Vector(*point)

                origin = FreeCAD.ActiveDocument.getObject("GeoOrigin")
                if origin: vector = vector.add(origin.Base)
                operations = self.terrain.Operations
                operations.append({"type":"Add Point", "index":index, "vector":vector})
                self.terrain.Operations = operations


class AddTriangle:
    """Command to add a triangle to Terrain."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/AddTriangle.svg",
            "MenuText": "Add Triangle",
            "ToolTip": "Add a triangle to selected Terrain."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return True

    def Activated(self):
        """Command activation method"""
        # Call for Mesh.Addfacet function
        FreeCADGui.runCommand("Mesh_AddFacet")


class DeleteTriangle:
    """Command to delete a triangle from Terrain."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/DeleteTriangle.svg",
            "MenuText": "Delete Triangle",
            "ToolTip": "Delete triangles from selected Terrain."
              }

    def IsActive(self):
        """Define tool button activation situation"""
        return True

    def Activated(self):
        """Command activation method"""
        # Create an event callback for delete() function
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.event_callback = self.view.addEventCallbackPivy(
            coin.SoButtonEvent.getClassTypeId(), self.delete)
        self.indexes = []

    def delete(self, cb):
        """Take two triangle by mouse clicks and swap edge between them"""
        # Get event
        event = cb.getEvent()

        # If mouse right button pressed finish swap edge operation
        if event.getTypeId().isDerivedFrom(coin.SoKeyboardEvent.getClassTypeId()):
            if event.getKey() == coin.SoKeyboardEvent.ESCAPE \
                and event.getState() == coin.SoKeyboardEvent.DOWN:
                self.view.removeEventCallbackPivy(
                    coin.SoButtonEvent.getClassTypeId(), self.event_callback)

        # If mouse left button pressed get picked point
        elif event.getTypeId().isDerivedFrom(coin.SoMouseButtonEvent.getClassTypeId()):
            if event.getButton() == coin.SoMouseButtonEvent.BUTTON1 \
                and event.getState() == coin.SoMouseButtonEvent.DOWN:
                picked_point = cb.getPickedPoint()

                # Get triangle index at picket point
                if picked_point:
                    detail = picked_point.getDetail()

                    if detail.isOfType(coin.SoFaceDetail.getClassTypeId()):
                        face_detail = coin.cast(
                            detail, str(detail.getTypeId().getName()))
                        index = face_detail.getFaceIndex()
                        self.indexes.append(index)

        # If mouse left button pressed get picked point
        if event.getTypeId().isDerivedFrom(coin.SoKeyboardEvent.getClassTypeId()):
            if event.getKey() == coin.SoKeyboardEvent.R \
                and event.getState() == coin.SoKeyboardEvent.DOWN:

                terrain = FreeCADGui.Selection.getSelection()[-1]
                copy_mesh = terrain.Mesh.copy()
                copy_mesh.removeFacets(self.indexes)
                self.indexes.clear()
                terrain.Mesh = copy_mesh


class SwapEdge:
    """Command to swap an edge between two triangles"""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/SwapEdge.svg",
            "MenuText": "Swap Edge",
            "ToolTip": "Swap Edge of selected Terrain."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return True

    def Activated(self):
        """Command activation method"""
        # Create an event callback for SwapEdge() function
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.face_indexes = []
        self.MC = FreeCADGui.ActiveDocument.ActiveView.addEventCallbackPivy(
            coin.SoButtonEvent.getClassTypeId(), self.SwapEdge)

    def SwapEdge(self, cb):
        """Take two triangle by mouse clicks and swap edge between them"""
        # Get event
        event = cb.getEvent()

        # If mouse right button pressed finish swap edge operation
        if event.getTypeId().isDerivedFrom(coin.SoKeyboardEvent.getClassTypeId()):
            if event.getKey() == coin.SoKeyboardEvent.ESCAPE \
                and event.getState() == coin.SoKeyboardEvent.DOWN:
                self.view.removeEventCallbackPivy(
                    coin.SoButtonEvent.getClassTypeId(), self.MC)

        # If mouse left button pressed get picked point
        elif event.getTypeId().isDerivedFrom(coin.SoMouseButtonEvent.getClassTypeId()):
            if event.getButton() == coin.SoMouseButtonEvent.BUTTON1 \
                and event.getState() == coin.SoMouseButtonEvent.DOWN:
                picked_point = cb.getPickedPoint()

                # Get triangle index at picket point
                if picked_point is not None:
                    detail = picked_point.getDetail()

                    if detail.isOfType(coin.SoFaceDetail.getClassTypeId()):
                        face_detail = coin.cast(
                            detail, str(detail.getTypeId().getName()))
                        index = face_detail.getFaceIndex()
                        self.face_indexes.append(index)

                        # try to swap edge between picked triangle
                        if len(self.face_indexes) == 2:
                            terrain = FreeCADGui.Selection.getSelection()[-1]
                            copy_mesh = terrain.Mesh.copy()

                            try:
                                copy_mesh.swapEdge(
                                    self.face_indexes[0], self.face_indexes[1])

                            except Exception:
                                print("The edge between these triangles cannot be swappable")

                            terrain.Mesh = copy_mesh
                            self.face_indexes.clear()
                            FreeCAD.ActiveDocument.recompute()


class SmoothTerrain:
    """Command to smooth Terrain."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/SmoothSurface.svg",
            "MenuText": "Smooth Terrain",
            "ToolTip": "Smooth selected Terrain."
            }

    def IsActive(self):
        """Define tool button activation situation"""
        return True

    def Activated(self):
        """Command activation method"""
        terrain = FreeCADGui.Selection.getSelection()[0]
        terrain.Mesh.smooth()


class TerrainEditGroup:
    """Gui Command group for the Arc tools."""

    def GetResources(self):
        """Set icon, menu and tooltip."""
        return {
            "Pixmap": icons_path + "/TerrainEdit.svg",
            "MenuText": "Edit Surface",
            "ToolTip": "Edit surfaces."}

    def GetCommands(self):
        """Return a tuple of commands in the group."""
        return ("Add Point",
                "Delete Triangle",
                "Swap Edge",
                "Smooth Terrain")

    def IsActive(self):
        """Return True when this command should be available."""
        if FreeCAD.ActiveDocument:
            selection = FreeCADGui.Selection.getSelection()
            if selection:
                if selection[-1].Proxy.Type == "Road::Terrain":
                    return True
        return False


FreeCADGui.addCommand("Add Point", TerrainAddPoint())
FreeCADGui.addCommand("Add Triangle", AddTriangle())
FreeCADGui.addCommand("Delete Triangle", DeleteTriangle())
FreeCADGui.addCommand("Swap Edge", SwapEdge())
FreeCADGui.addCommand("Smooth Terrain", SmoothTerrain())
FreeCADGui.addCommand("Terrain Edit", TerrainEditGroup())